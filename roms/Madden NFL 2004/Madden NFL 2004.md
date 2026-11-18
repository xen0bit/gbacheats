# Madden NFL 2004 (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Madden NFL 2004.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `MADDEN NFL04` |
| Game code | `BMDE` |
| Maker | `69` (EA) |
| Version / complement / checksum | `0x00` / `0xBD` / `0x0000` |
| Entry word | `0xEA00002E` (stock GBA `b 0xC0`) |
| MD5 | `197dc540682b32e2022fec2ec543be1a` |
| SHA-1 | `8c932f469d7d66f604fa6a34adfa3acea5b7f63e` |
| SHA-256 | `a5a607535a377b55822a5e1dc7a309c723d7334dc346cdd3d19ff94766e63e31` |

Phase 0 notes (**Derived** from header bytes): the Nintendo-logo bytes at `0x04` are
non-standard (`24 ff ae 51 69 9a a2 21 …`), and the header checksum is `0x0000` —
the usual signature of a rebuilt/emulator-patched header (guide §16.1). The entry
word and the first 4 KiB are a normal ARM crt0 (`mov r0,#0x12` / `msr`), **not** a
cracktro. A full-file scan for the 156-byte logo found exactly **one** header at
file `0x0`: no multi-game image, multiboot stub, appended trainer, or patched cheat
menu. SKU confirmed as the U.S. GBA release (BMDE), so console/PC cheat lists for
the same franchise title are *not* automatically applicable (§16.11).

## 2. Executive summary

**No in-game password, cheat-code, button-code, or hidden debug-menu system exists
in this GBA SKU.** There is no password entry screen, no code table, no validator,
and no reachable developer menu. The game's only "cheat-like" content is:

* four *hidden teams* (data only: `All-Madden`, `Players, Inc.`, `EA Sports`, `Budcat`)
  and a *hidden quarter length* (15 seconds), both reachable only by CodeBreaker
  RAM patches on TCRF — **not** by any controller input; and
* gameplay glitches/hints and a GameCube-link Madden Cards feature published on
  cheat sites — not developer-intended unlock codes.

Every reachable screen was walked (title, PLAY NOW→Solo/Link, Team Select, Game
Rules, Controller Setup, actual gameplay, SEASON PLAY and its three screens,
FRONT OFFICE and its four screens, EXTRAS and its two screens) with savestate RAM
evidence. The two published controller sequences that could plausibly be codes
were both entered and **rejected by RAM evidence**: `L,L,R,R,Select` at Game Rules
and at Season Rules (the documented 2002/2003 quarter-length code) left
`0x02000524` unchanged and revealed no new option, and `A,R` repeated in a live
game produced no first down. The option/team spaces are closed: 4 of 5 quarter
values and 32 of 36 team IDs are reachable, with the hidden values provably
unreachable by cycling. The input/key space was searched with counts (below).

Per §0.2, the deliverable is a **bounded, reproducible negative**, not a
"not looked hard enough" claim.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 SDL, `Xvfb :316`, `SDL_AUDIODRIVER=dummy`, `-3` scaling.
* Keymap (verified by driving menus): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, D-pad=arrow keys. Hold ~100–150 ms per press.
* Work on a **copy** of the ROM so the shipped folder stays free of `.sav`/`.ss1`.
* RAM evidence: mGBA savestates (`Shift+F1`). A `.ss1` is a PNG with a zlib
  `gbAs` chunk; decompressing yields a 397,312-byte (`0x61000`) state in which
  EWRAM begins at `0x21000`, IWRAM at `0x19000`, VRAM at `0x1000`. GBA RAM
  address → state offset: `0x02xxxxxx → 0x21000+(addr-0x02000000)`,
  `0x03xxxxxx → 0x19000+(addr-0x03000000)`.
* Exact menu path used: title → PLAY NOW → SOLO PLAY → Team Select (HOME/VISITOR)
  → Game Rules → Controller Setup → kickoff/live play; title → SEASON PLAY →
  New NFL Season / New Playoffs / Season Rules; title → FRONT OFFICE → Create a
  Player / Trade Players / Reset Rosters / Delete Players; title → EXTRAS →
  Records / Madden Cards.
* Codes tested: `L,L,R,R,Select` at Game Rules and Season Rules; `A,R` ×8 in a
  live 1st-and-10 game; plus seven title-screen sequences (below).

## 4. Address map

All file offsets are `.gba` offsets; ROM address = `0x08000000 + file offset`.

| Item | File offset | ROM/RAM address | Evidence |
|---|---|---|---|
| Key-read routine (reads `0x04000130`) | `0x1330` | `0x08001330` (Thumb) | Derived (Capstone) |
| `KEYINPUT` literal | `0x1380` | `0x08001380` → `0x04000130` | Derived |
| Input edge/update routine | `0x12DC` | `0x080012DC` (Thumb) | Derived |
| Button-remap helper | `0x11E0`–`0x1226` | `0x080011E0` (Thumb) | Derived |
| Held key mask (`~KEYINPUT & 0x3FF`) | — | `0x02027258` (u16) | Derived + Observed |
| Key pressed/edge masks | — | `0x02020A7C/7E/80/82` | Derived |
| Home team ID | — | `0x02000520` (u16) | Observed |
| Visitor team ID | — | `0x02000522` (u16) | Observed |
| Quarter-length index | — | `0x02000524` (u16) | Observed |
| EWRAM generic-write helper (watchpoint hit) | — | `0x03001338`–`0x03001356` (IWRAM, ARM) | Observed |
| Script-VM opcode dispatcher (example) | — | `0x03002900`–`0x03002BFC` (IWRAM, ARM) | Derived |
| In-game commentary strings | `0x2C0158`+ | `0x082C0158`+ | Observed |
| Credits strings | `0x3A7D9F`+ | `0x083A7D9F`+ | Observed |

The lack of a ROM literal for `0x02000524` is explained by the engine: code is
copied to IWRAM and the write is made through a generic helper with the address
built in a register (`lsl r3,r1,#0x10; mov r2,#0x02000000; add r3,r2,r3,lsr#16`).
A write watchpoint on `0x02000524` hit at IWRAM `0x0300134C` with
`r3 = 0x02000524`, `r14 = 0x03002990`, confirming the path.

## 5. Algorithm

Input path (**Derived** from disassembly of `0x08001330` and `0x080012DC`):

```
held = ~(*(volatile u16*)0x04000130) & 0x3FF      // active-high; A=1,B=2,Sel=4,
                                                   // Start=8,R=0x10,L=0x20,U=0x40,
                                                   // D=0x80,RTrig=0x100,LTrig=0x200
*(u16*)0x02027258 = held
pressed = held & ~old_held                         // 0x080012DC
*(u16*)0x02020A7C/7E/80/82 = derived edge/hold states
```

Active-high mask convention confirmed by the code at `0x08001344`:
`eors r4, r1` with `r2 = 0x3FF`. UI screens are rendered by a bytecode VM whose
interpreter is copied to IWRAM (`0x0300xxxx`); the quarter-length and team fields
are written by its opcodes, which is why no button-sequence table appears as a
plain u16 array in ROM.

Quarter-length setter (observed by watching `0x02000524` while pressing Left/Right
on Game Rules): cycling is `0 → 1 → 2 → 3 → 0`; the field is a u16 index, not a
duration. Team selector (`0x02000520`/`0x522`): Down/Up changes the focused
team, Left/Right switches HOME/VISITOR; the value wraps `32 → 1`.

## 6. Tables

**Quarter-length values** (`0x02000524`, Observed):

| Index | Label shown |
|---:|---|
| 0 | 5 MINUTES (default) |
| 1 | 10 MINUTES |
| 2 | 15 MINUTES |
| 3 | 3 MINUTES |
| 4 | *hidden* — TCRF says 15 seconds at `0x02000524 = 04`; not selectable |

**Team IDs** (`0x02000520` / `0x02000522`, Observed for 1–32; TCRF for the rest):

| ID | Team |
|---:|---|
| 1–32 | the 32 NFL teams (cyclable; wrap at 32→1) |
| `0x00` | All-Madden (*hidden*) |
| `0x21` | Players, Inc. (*hidden*) |
| `0x22` | EA Sports (*hidden*) |
| `0x23` | Budcat (*hidden*) |

TCRF's CodeBreaker notation `00xx` with `xx = 21/22/23` is **hexadecimal**;
the working values are `0x21/0x22/0x23` (= 33/34/35 decimal), which is why they
lie just outside the reachable 1–32 range.

**Input masks**: `A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010,
Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200` (active-high).

## 6b. Enumeration

**Code-space size.** This game has no password/checksum code space and no
button-code action dispatcher, so the "space" is the set of reachable menu values
plus the set of controller sequences that can be entered at a screen:

* Quarter-length field: 5 possible u16 values (`0..4`); **4 reachable**, value 4
  hidden. Bounds proven by the full cycle `0→1→2→3→0` captured with RAM reads
  (11 consecutive Right presses) and by the failed button-code tests.
* Team fields: 36 possible IDs (`0`, `1..32`, `0x21`, `0x22`, `0x23`); **32
  reachable**. Bounds proven by 40 consecutive Down presses (`23→32→1→…→31`),
  with the selector wrapping at 32 and never producing 0, 33, 34 or 35.
* Button sequences: the complete input alphabet has 10 buttons; the two published
  sequences were tested at every screen where they could apply, plus seven
  title-screen sequences (`L,L,R,R,Select`; Konami code; `L,R,A`; `Select,A`;
  Konami without B/A; `A`×5; `L,R,L,R,B,A`). **No new screen or state appeared** —
  the title sweep only navigated ordinary menus / typed into the Create-a-Player
  NAME field (e.g. `NAME: AAAAAAAA`, no effect).
* Literal/button-space search counts (whole 4 MiB unless noted):
  - `0x04000130` literal: **2** hits (`0x1380`, `0x1A68`) — both in the input
    system, no third consumer such as a cheat validator.
  - Runs of ≥5 consecutive u16 single-bit key masks: **427** whole-ROM, **21**
    in the code region (`0x00000–0x7FFFF`); the 2003 reference ROM has 17 there.
    All 2004 runs are the same shared controller-icon/input data as 2003; none
    decode to `L,L,R,R,Select` (`0x200,0x200,0x100,0x100,0x004`) in either
    active-high, active-low, inverted, reversed or byte/index encodings.
  - Password/code/debug keyword hits in `strings -t x -n 4`: **1** genuinely
    relevant ASCII hit in the whole ROM (`KICKING TEAM` at `0x3A7466`); UI text
    is script/tile-indexed, not ASCII (see §7).

**Novel code.** Not applicable — there is no code system from which to mint a
novel value. This is the bounded §0.2 negative case: the two content items the
community treats as cheats (hidden teams, 15-second quarters) are shown to be
*data without an input path*, and the published controller sequences are shown
to be non-functional on this SKU.

**Bounds proven by rejection.** (1) `L,L,R,R,Select` at Game Rules: `0x02000524`
read `0x0001` before and after; cycling still yielded exactly the 4 known labels.
(2) Same sequence at Season Rules: `0x524` read `0` before and after; no new
option. (3) `A,R` ×8 in a live 1st-and-10 game: `0x02000520/522/524` unchanged
(`0x0006 / 0x0017 / 0`), no first-down awarded; the game returned to Controller
Setup. (4) Hidden value 4 could be forced by debugger RAM write
(`w/2 0x02000524 0x4`, readback `0x0004`) but no UI route produces it.

## 7. Validation evidence

**Observed** (emulator + savestate RAM):
* Title/menu/gameplay screens listed in §3; PLAY NOW → game reached with scoreboard
  RAIDERS 0 / BUCCANEERS 0, kickoff, a live 1st-and-10 play, commentary
  (`A KICK OF 64 YARDS / A. STECKER RUNS FOR A GAIN OF 25`).
* `0x02000520=0x0006` (Buccaneers HOME), `0x02000522=0x0017` (Raiders VISITOR)
  at Team Select; team cycling produced IDs 1–32 only.
* Quarter index at `0x02000524` taking exactly 0/1/2/3 via D-pad; RAM reads before
  and after both published button sequences.
* EXTRAS → Madden Cards shows `ATTEMPTING TO CONNECT TO NINTENDO GAMECUBE™`
  (gated by link hardware; not a cheat screen). EXTRAS → Records has `SELECT: RESET`.
* Debugger write watchpoint on `0x02000524` hit at IWRAM `0x0300134C` with
  `r3=0x02000524`, `r14=0x03002990` (captured CPU state).

**Derived** (disassembly): key-input routine `0x08001330`, edge routine
`0x080012DC`, remap helper `0x080011E0`, script-VM opcodes in IWRAM, the mask
convention, and all literal/xref counts in §6b.

**Inferred** (clearly labelled): the quarter value 4 = 15 seconds (TCRF's claim;
I proved the field accepts 4 but did not run a full 15-second quarter), and the
existence/purpose of the four hidden teams (TCRF; I proved they are outside the
UI cycle). No inference is presented as an observation.

**Font/tile-indexed text check (negative bounded).** `strings` finds only
commentary (`0x2C0158`+) and credits (`0x3A7D9F`+) in ASCII; no UI label. I
searched the whole ROM for `5 MINUTES`, `15 SECONDS`, `QUARTERS`, `GAME RULES`,
`TEAM SELECT`, `ALL-MADDEN`, `DEBUG`, `PASSWORD`, `CHEAT`, etc. in ASCII, lowercase,
`+0x20`, `-0x20`, UTF-16LE, UTF-16BE and all 256 one-byte tile-index bases —
**zero hits**. VRAM tilemaps in the savestate (`0x06000000`, `0x06000800`) decode
to graphical background art (EA watermark), not text; the UI is drawn by the
script VM from tile indices, so ASCII `strings` absence is not evidence of a
missing feature — but the complete menu enumeration above is.

**Published-code verification:**
* GameFAQs GBA page (archived) — "1 cheat", but the body lists mostly GC/PS2/Xbox
  glitches/unlockables; no GBA password or button code.
* ChapterCheats — "First down for opposite team: Press A, R repeatedly" (GBA) and
  a Washington-Redskins-playbook substitution glitch. The A,R sequence was tested
  (rejected); the substitution item is a gameplay glitch, not a code.
* TCRF — hidden teams, hidden quarter length, and an explicit *"See if there are
  button codes for these"* TODO. I closed that TODO negatively for both.
* CheatBook / Neoseeker / Supercheats / Almar's — GameShark/CodeBreaker or
  console/PC hints; out of scope (memory-edit codes, different SKUs).
* Fetched pages were treated as data; no prompt-injection payload was encountered.

## 8. Unknowns

* LINK PLAY was observed in the PLAY NOW menu but not entered (requires a
  GameCube link cable); it is not a cheat surface at the menu level.
* The exact label for hidden quarter value 4 was not displayed: writing
  `0x02000524 = 4` with the debugger changed the RAM value (readback `0x0004`)
  but the Game Rules screen kept showing `5 MINUTES`, because the label is drawn
  from the script VM's cached state. The 15-second semantics remain TCRF-sourced.
* The hidden teams' rosters/graphics were not extracted; only their IDs and
  unreachability were established.

## 9. Tooling

* `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, Python byte scans.
* `capstone` 5.0.7 + `keystone-engine` (installed via `pip --break-system-packages`)
  for Thumb/ARM disassembly of `0x080011C0–0x08001520` and IWRAM `0x03001200+`.
* mGBA 0.10.5 SDL under Xvfb `:316` with openbox; xdotool for input; `scrot` +
  ImageMagick `convert`/`montage` for screenshots (kept on disk, ≤20 read).
* `ssread.py` (savestate `gbAs` zlib decoder + GBA→state RAM mapping), `step.sh`
  (press/screenshot/savestate helper), `mgba_dbg.py` / `quick_dbg.py`
  (mGBA `-d` CLI debugger driven through a PTY; used for live RAM reads/writes
  and the write watchpoint). The GDB stub (`-g`) was unusable because port 2345
  was held by another concurrent analysis session, so the CLI debugger and
  savestate diffing were used instead (guide §16.13).

**Legal note:** no ROM bytes, extracted graphics, or game assets are reproduced
here — only hashes, addresses, algorithms, counts, and original observations.
