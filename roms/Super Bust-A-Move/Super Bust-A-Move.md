# Super Bust-A-Move (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Super Bust-A-Move/Super Bust-A-Move.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `BUSTAMOVEGBA` |
| Game code | `ABME` (maker `41`), version `0x00` |
| Entry word | `0xEA00002E` — **stock** crt0, no cracktro/trainer patch |
| Header checksum | `0x0000`; complement byte `0x57` |
| MD5 | `00b3169c025d8000f8944e2e8b81c2b5` |
| SHA-1 | `bf8f61b61e1a8f4a32ae27d4483a44fdd08477fb` |
| SHA-256 | `c4f8cc995c5bc369264cbab72ae01d9fee60e33cd3c210bf5860ccb704194e9a` |

`file(1)` reports "Game Boy Advance ROM image: "BUSTAMOVEGBA" (ABME41, Rev.00)".
The complement byte is non-zero, so this is not the zeroed-complement rebuild
pattern of guide §16.1.

## 2. Executive summary

The game has **exactly two developer-intended button codes**, both entered on the
**title screen ("PRESS START")**, and no password/code-entry field:

* **A, R, L, A** — unlocks the two secret characters.
* **B, R, L, B** — unlocks Extra Mode (bonus levels / the "EXTRA" indicator).

Both are published on 3rd party cheat indexes, and both were verified in the
emulator with RAM evidence. The implementation is a tiny hard-coded table at
`0x080902E8` (16 bytes = 2 codes × 4 button masks) plus a validator at
`0x08030FA0`. There is no checksum, no alphabet, no generator and no second
code system: every action branch and every table entry were enumerated from the
disassembly. The code names also survive as literal strings `ARLA` and `BRLB` in
the ASCII message bank at `0x083DEA6C`/`0x083DEA71`.

The accepted 4-press space is **exactly 2 sequences out of 10,000 possible
single-button 4-press sequences** (10-button set). Undocumented combinations —
including the natural "both codes at once" chord **A+B, R, L, A+B** — are
*rejected*: the validator clears both progress counters before the accept test,
so an extra button at any step aborts the run. This is a bounded negative
(§0.2), not an untested gap. No GameShark/Action Replay/CodeBreaker codes are
reported; the Action Replay list at 3rd party cheat indexes are out of scope.

## 3. How to reproduce

* Emulator: `mgba 0.10.5`, `DISPLAY=:317`, `SDL_AUDIODRIVER=dummy`, `-3` scale,
  Xvfb + openbox. Command-line debugger `-d` used for RAM reads (the GDB stub
  port 2345 was occupied by another session).
* mGBA SDL keymap used: **A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`,
  Select = `BackSpace`**, d-pad = arrow keys. Hold ≈150 ms per press.
* Boot path → `LANGUAGE SELECT` (English default) → press **A** →
  title `PRESS START`.
* Enter a code at the title screen, one button per press, no extra buttons held:
  `x s a x` (A,R,L,A) or `z s a z` (B,R,L,B).
* Read RAM with mGBA savestates (`Shift+F9` writes `game.ss9`), decompressing the
  PNG `gbAs` chunk per guide §16.13: IWRAM at raw offset `0x19000`, EWRAM at
  `0x21000`.
* Screens walked (baseline and after unlocks): `LANGUAGE SELECT` (5 languages in
  the bank: ENGLISH/FRENCH/GERMAN/SPANISH/ITALIAN) → title → `GAME MENU`
  (4 entries: 1P PUZZLE, CPU BATTLE, 2P BATTLE, OPTION) → `MODE SELECT` for 1P
  PUZZLE (TRAINING/NORMAL/CLASSIC) → stage-select map (nodes A–I) → `MODE SELECT`
  for CPU BATTLE (NORMAL/EXPERT) → `PLAYER SELECT` character grid → `OPTION`
  (GAME SETTING / SCORE RANKING / BATTLE RESULT / EXIT) → `GAME SETTING`
  (MATCH POINT, GUIDE LINE, EXIT); plus in-game HUD/pause/results screens.

## 4. Address map

| Address | File offset | Meaning |
|---|---|---|
| `0x080902E8` | `0x902E8` | **Code table**, 16 bytes: `[0x0001,0x0100,0x0200,0x0001]` (A,R,L,A), `[0x0002,0x0100,0x0200,0x0002]` (B,R,L,B), each `u16` little-endian |
| `0x080902F8` | `0x902F8` | Literal pointer to `0x080902E8` (self-reference in the surrounding data block) |
| `0x08030FA0` | `0x30FA0` | **Validator** (called once per title-screen frame from `0x080305F0`) |
| `0x08031148` | `0x31148` | Literal pool: `0x080902E8` (table base) |
| `0x0803114C` | `0x3114C` | Literal pool: `0x030004AE` (active-high key mask) |
| `0x08031150` | `0x31150` | Literal pool: `0x02003C04` (progress A byte; `+1` = progress B) |
| `0x08031154` | `0x31154` | Literal pool: `0x02003C06` (last-advanced code index, 0 or 1) |
| `0x08031158` | `0x31158` | Literal pool: `0x02003C00` (unlock flags byte) |
| `0x02003C00` | — | Flags: bit `0x01` = secret characters, bit `0x02` = Extra Mode |
| `0x02003C04` / `05` | — | Progress counters for code A / code B (0–4) |
| `0x02003C06` | — | Code index (0 = A, 1 = B) |
| `0x030004AE` | — | `u16` active-high key mask: A=1, B=2, Select=4, Start=8, →=0x10, ←=0x20, ↑=0x40, ↓=0x80, R=0x100, L=0x200. Live read with A held returned `0x0001`; `KEYINPUT` `0x04000130` = `0x03FE`. |
| `0x08030D50` | `0x30D50` | Effect for A,R,L,A: message + sets secret-character bits in global struct `0x03000024`, plays sound 22 |
| `0x08030B68` | `0x30B68` | Effect for B,R,L,B: message + sets Extra bits (`0xF0` at `+0x58`, `0xA0` at `+0x38`) in `0x03000024`, plays sound 21 |
| `0x080022EC` | `0x22EC` | Sound/message dispatcher (`r0`=sound id) |
| `0x083DEA6C` / `0x083DEA71` | `0x3DEA6C` / `0x3DEA71` | ASCII strings `ARLA\0` / `BRLB\0` (message table records `{len=5, ptr, id=0x495A}` at `0x083DEA78`) |
| `0x083DC000–0x083DEB00` | same | ASCII text bank (all UI labels and localized variants) |

## 5. Algorithm

Reimplementation of `0x08030FA0` (evidence: Thumb disassembly, confirmed by RAM
diffs):

```python
TABLE = [1,0x100,0x200,1, 2,0x100,0x200,2]   # u16 @ 0x080902E8, 8 entries
flags = byte[0x02003C00]
pA, pB = byte[0x02003C04], byte[0x02003C05]
idx    = byte[0x02003C06]          # 0 = code A, 1 = code B
keys   = u16[0x030004AE]           # active-high mask

# 1) exact-match gate: any button outside the expected mask aborts
expected = TABLE[idx*4 + (pB if idx else pA)]
if keys & ~expected & 0x3FF:
    pA = pB = idx = 0              # reset BOTH progresses

# 2) code A branch (A,R,L,A)
if not (flags & 1) and (keys & TABLE[0 + pA]):
    if pA == 0: pB = 0             # starting A cancels B
    idx = 0
    pA += 1
    if pA == 4:
        flags |= 1
        effect_0x08030D50(flags); sound(22)

# 3) code B branch (B,R,L,B)
if not (flags & 2) and (keys & TABLE[4 + pB]):
    if pB == 0: pA = 0             # starting B cancels A
    idx = 1
    pB += 1
    if pB == 4:
        flags |= 2
        effect_0x08030B68(flags); sound(21)
```

Properties:

* The validator reads **held** keys, not edges. Holding one button cannot
  advance twice, because the second frame's expected mask has changed and the
  mismatch gate resets the counter first.
* The mismatch gate runs **before** both accept branches. Therefore an extra
  button at any step (including the last) resets progress to 0 before the
  branch sees it — only exactly-one-button presses can complete a code.
  This is what rejects chords and "wrong last button" inputs.
* Branches are skipped once their flag bit is set: each code fires once.
* The two branches are mutually exclusive per first press (each resets the
  other's counter), so you cannot interleave halves of the two codes.
* Sequence length is fixed at **4** (`cmp r1,#4` twice, at `0x08030800` and
  `0x08031116`); there is no shorter or longer variant.

## 6. Tables

| Code | Mask sequence | ROM table bytes | Flag bit | Effect |
|---|---|---|---|---|
| A,R,L,A | `01 00 00 01 00 02 01 00` | `0x080902E8` | `0x01` @ `0x02003C00` | 2 secret characters (`0x08030D50`, sound 22) |
| B,R,L,B | `02 00 00 01 00 02 02 00` | `0x080902F0` | `0x02` @ `0x02003C00` | Extra Mode / bonus levels (`0x08030B68`, sound 21) |

Button mask encoding (active-high, `~KEYINPUT & 0x3FF`):
A `0x001`, B `0x002`, Select `0x004`, Start `0x008`, Right `0x010`, Left `0x020`,
Up `0x040`, Down `0x080`, R `0x100`, L `0x200`.

The ASCII text bank contains the internal code names: `ARLA` at `0x083DEA6C`
and `BRLB` at `0x083DEA71`. No other code-like string (`password`, `cheat`,
`debug`, `level select`) exists in the ROM; the only `EXTRA` strings are
localized mode labels (`NORMAL EXTRA`, `CLASSIC EXTRA`, `EXPERT EXTRA` at
`0x083DD2C4`–`0x083DD4B7`), consistent with the Extra Mode unlock.

## 6b. Enumeration

**Space definition.** The entire cheat surface is a 16-byte table (2 records ×
4 `u16` masks) and a 2-branch validator. With the 10-button set there are
`10^4 = 10,000` possible 4-press sequences; **2** are accepted, both published.
Because the validator is called only from the title-screen routine
(`BL 0x08030FA0` at `0x080305F0`), the codes are only reachable there.

**Validator model.** Section 5's pseudocode was run mentally and checked against
five live inputs; every observed flag/progress/index value matched.

**Published-code verification (accepted):**

| Input | Flags `0x02003C00` | Progress | Screenshot |
|---|---|---|---|
| A,R,L,A (`x s a x`) | `0x01` | pA=4, idx=0 | `pub_ARLA_gba.png` — new character icon bottom-left; `arla_charsel_gba.png` — secret characters in PLAYER SELECT |
| B,R,L,B (`z s a z`) | `0x02` | pB=4, idx=1 | `pub_BRLB_gba.png` — new EXTRA icon bottom-right of GAME MENU; `extra_modesel_gba.png` |

**Novel, unpublished combinations — pressed in the emulator, all rejected:**

| Input | Result | Evidence |
|---|---|---|
| **A+B, R, L, A+B** (both codes' prefixes held together — an obvious undocumented combination) | flags `0x00`, pA=1, pB=1, idx=1 — rejected | `novel_chord_gba.png`; RAM capture `game.ss9` |
| A, R, L, **B** (wrong final button) | flags `0x00`, pA reset to 0, pB=1, idx=1 — rejected | `rej_ALB_gba.png` |

The chord result is explained exactly by §5: at the final step `idx=1` (code B
last advanced), so the expected mask is B; the extra A trips the mismatch gate,
which zeroes both counters *before* the accept branches run. Progress therefore
goes 3 → 0 → 1 instead of 3 → 4. **No novel accepted code exists** — the table
has two entries and the validator has two action branches; this is a proven
bounded negative, not an untested possibility. The "secret characters" and
"Extra Mode" effects were confirmed on their real screens with real keyboard
input, not by debugger calls.

**Bounds proven by rejection / derivation:** wrong final button and extra
simultaneous button were rejected live (table above); a 3-press partial sequence
leaves flags 0 (observed en route to every test); the validator has a single
caller — the title-screen routine (`BL` at `0x080305F0`, no others) — so codes
are unreachable from other screens (derived, not live-tested). The mismatch gate
also rejects any held extra button at every step.

## 7. Validation evidence

* **Observed** — boot/screenshots; key state `0x030004AE = 0x0001` with A held
  and `KEYINPUT = 0x03FE`; savestate RAM captures for all five inputs; secret
  character icons and EXTRA icon appearing after the respective codes.
* **Derived** — table layout, literal pointers, branch structure and flag bit
  meanings from Thumb disassembly of `0x08030FA0`, `0x08030D50`, `0x08030B68`
  and caller `0x080305F0`; every observed RAM value agrees with the model.
* **Inferred** — the exact `EXTRA` level set added by B,R,L,B was not exhaustively
  counted; the stage-select map looked identical before and after, so the
  unlocked stages may be appended behind progression or only labelled in
  results. The visible Game Menu indicator proves the unlock flag was set.

## 8. Unknowns

* Which specific stages/characters the two unlocks add, and whether the stage
  map gains nodes after clearing existing levels (not exhaustively played).
* The role of the `ARLA`/`BRLB` strings in the message table at `0x083DEA78`
  (they are stored as `{len=5, ptr, id=0x495A}` records; no display path was
  isolated). They are treated as internal code names, not a third code system.
* No hidden debug menu was found: no `debug`-style strings in the fully
  enumerated ASCII bank (`0x083DC000–0x083DEB00`), and no additional code table
  is referenced by the title-screen validator.

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  for Thumb disassembly.
* Capstone 5.0.7 + Python for `u16` literal/sequence scans and literal-pool
  verification (`struct.unpack_from("<I", ...)`, per guide §11).
* `mgba -3 -d` under Xvfb :317/openbox, driven by a Python pty server
  (`pty_server.py`, `dbg.py`) for startup breakpoints and `r/1`/`r/2` reads;
  `keys.py` (xdotool XTEST) for real input; `scrot` + ImageMagick for captures.
* `ssread.py`: PNG `gbAs` chunk zlib decompression and GBA→raw offset mapping
  for RAM reads (guide §16.13); `testseq.py` for load-input-capture cycles.
* No ROM or copyrighted assets are redistributed; only addresses, hashes,
  algorithms and our own screenshots are reported.
