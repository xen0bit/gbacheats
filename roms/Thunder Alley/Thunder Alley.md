# Thunder Alley (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Thunder Alley/Thunder Alley.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `THUNDERALLEY` |
| Game code / maker | `BTHE` / `FS` |
| Revision | `0x00` (Rev.00); fixed byte `0x96`, header checksum `0x0004` |
| Entry word | `EA00002E` → `0x080000C0` (stock crt0; no scene cracktro — §16.1 check passed) |
| MD5 | `afcd7bcfdc31ae934333da25db6107c0` |
| SHA-1 | `d63aaf9ac4468f1d0ead35606d9a4f56327b2537` |
| SHA-256 | `a36d8b077397c25064bd90bf10c28e0f0fcdfba2add23b3ba6cc33ad408b93de` |

## 2. Executive summary

The game has **one developer-intended button code** on the **title screen**: the
Konami sequence `↑ ↑ ↓ ↓ ← → ← → B A`. It unlocks the fourth main-menu entry
**Demolition Derby** (a "Stay Alive!" demolition mode). The game itself ships the
hint as plaintext in the ROM at `0x0802A0BC` ("Secret Gameplay Mode / from the
Title Screen / Up, Up, Down, Down / Left, Right, Left, Right / B Button, A Button"),
and published lists (SuperCheats, cheatingdome, a German emulation wiki) agree.

The validator is a **fixed 10-mask sequence matcher** at `0x0800F4E4`. It compares
the *newly-pressed key mask* against a 10-entry `u16` table at `0x08062FD8` using
**bitwise AND ≠ 0**, not exact equality. This is the interesting surface: extra
buttons pressed in the same frame are ignored, so many undocumented chords also
unlock the mode. Two novel 10-press sequences were minted and accepted in the
emulator (§6b), with in-game proof (flag byte and menu screenshot).

There is **no password system, no alphabets/tables of textual codes, no checksum
and no debug menu reachable from retail input** in this image. The accepted outcome
space is a single flag bit. GameShark/CodeBreaker/Action Replay codes listed on
GameHacking.org are external cheat-device codes and were **not** analysed (out of
scope).

## 3. How to reproduce

* mGBA 0.10.5 under Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, `-3` scaling.
* SDL keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. Hold each key ~70–90 ms with ~220–300 ms gaps; menu
  navigation needs short holds (150 ms double-steps, §16.2).
* `xdotool` chords must use `keydown --delay 0` for every key in one process;
  xdotool's default 12 ms inter-command delay straddles a 60 Hz frame and turns
  a chord into separate presses.
* Menu path: title screen → enter code → Start → main menu (now 4 entries) →
  Demolition Derby → character → track map → "Stay Alive!" race.
* Savestate slot 1 holds a pristine title state (`flag=0, index=0`); every code
  test loads slot 1, sends the sequence, saves a state, and reads RAM from the
  decompressed `gbAs` chunk.

Published/known sequence used as decoder anchor:

```
UP UP DOWN DOWN LEFT RIGHT LEFT RIGHT B A
```

Novel sequences (absent from every published list) in §6b.

## 4. Address map

| Address | File offset | Meaning | Evidence |
|---|---:|---|---|
| `0x08062FD8` | `0x062FD8` | 10×`u16` expected key-mask table (Konami) | literal search + ROM dump |
| `0x0800F4E4` | `0x00F4E4` | Title-scene handler containing the validator (installed as Thumb ptr `0x0800F4E5` at `0x08061B50`) | disassembly |
| `0x0800F348` | `0x00F348` | Scene handler that draws the in-ROM "Secret Gameplay Mode" hint text (ptr `0x0800F349` at `0x08061CA0`) | disassembly + pointer |
| `0x0800E788` | `0x00E788` | Reader of the unlock flag; when set writes `0x50/0x64/0x8C` into three racer records at `+0x39` | disassembly |
| `0x0802A0BC` | `0x02A0BC` | Plaintext hint strings (5 lines) | `strings -t x` |
| `0x03003878` | — | Held key word = `~KEYINPUT`; observed `0xFC00` idle → `0xFC40` with Up | savestate diff |
| `0x03003880` | — | Edge-triggered "pressed this frame" mask consumed by validator | validator literal `0x0800F638` |
| `0x03003810` | — | Progress index (`u8`), 0…10 | validator literals; RAM |
| `0x03004B64` | — | Unlock flag (`u8`), set to 1 on success | validator literal; RAM |

Savestate layout used for RAM reads (mGBA 0.10.5, 4 MiB ROM, 397,312-byte `gbAs`):
IWRAM `0x03000000` → file `+0x19000`; EWRAM `0x02000000` → `+0x21000`.

## 5. Algorithm

Validator at `0x0800F4E4` (Thumb), per frame on the title screen:

```python
TABLE = [0x40,0x40,0x80,0x80,0x20,0x10,0x20,0x10,0x02,0x01]  # 0x08062FD8
idx   = ram.u8(0x03003810)   # progress
press = ram.u16(0x03003880)  # newly-pressed mask this frame (~KEYINPUT edge)

if idx < len(TABLE) and (press & TABLE[idx]) != 0:
    idx += 1
    ram.u8(0x03003810) = idx
    if idx == 10:
        ram.u8(0x03004B64) = 1       # unlock
        ram.u8(0x03003810) = 0       # reset progress
        call(0x08022A2C)             # feedback (sound)
elif press != 0:
    ram.u8(0x03003810) = 0           # wrong press resets progress
# else: no press -> progress unchanged
```

Key details derived from `0x0800F5E2`–`0x0800F658`:

* `0x0800F5F0`: `ldrh r0,[0x03003880]`, `ldrh r1,[table+idx*2]`, `ands`, test
  non-zero → **mask intersection**, not equality.
* `0x0800F60E`: `idx++`; `0x0800F614`: `cmp r1,#10`; on equal `0x0800F61C`
  stores `1` to `0x03004B64`, zeroes `idx`, calls `0x08022A2C`.
* `0x0800F64C`–`0x0800F658`: on mismatch, if the pressed word is non-zero,
  zero `idx` (releasing the keys alone never resets).
* Only **one** action branch exists: `flag=1`. The table has exactly 10 entries;
  the word after it (`0x2007` at `0x08062FEC`) is unrelated data, never indexed.

Effect chain: `0x0800E788` loads the flag; if non-zero it branches to
`0x0800E7D8`, which writes `0x50` (80), `0x64` (100) and `0x8C` (140) to the
`+0x39` byte of three racer records. Observed user-visible effects: title
"Press START" turns red; the main menu gains **Demolition Derby**; entering it
reaches a "Stay Alive!" mode.

## 6. Tables

Key masks (GBA `KEYINPUT` active-high, `~KEYINPUT & 0x3FF`):

| Button | Mask | Button | Mask |
|---|---:|---|---:|
| A | `0x001` | Right | `0x010` |
| B | `0x002` | Left | `0x020` |
| Select | `0x004` | Up | `0x040` |
| Start | `0x008` | Down | `0x080` |
| R | `0x100` | L | `0x200` |

Code table at `0x08062FD8` (`u16` LE):

| Index | Mask | Button | Index | Mask | Button |
|---:|---:|---|---:|---:|---|
| 0 | `0x040` | Up | 5 | `0x010` | Right |
| 1 | `0x040` | Up | 6 | `0x020` | Left |
| 2 | `0x080` | Down | 7 | `0x010` | Right |
| 3 | `0x080` | Down | 8 | `0x002` | B |
| 4 | `0x020` | Left | 9 | `0x001` | A |

Published recon (treated as data):

| Source | Claim | ROM verification |
|---|---|---|
| SuperCheats | "At the Title screen input Up, Up, Down, Down, Left, Right, Left, Right, B, A" → unlock Demolition Mode | Exact sequence present at `0x08062FD8`; accepted with `flag=1` |
| cheatingdome | "Demolition Mode" | Observed menu entry "Demolition Derby" |
| classicemu (DE) | "up up down down left right left right B A" → "unlimited time mode" | Same sequence; effect is the Demolition Derby mode |
| GameHacking.org | Only GameShark/CB/AR codes ("Unlock Demo Derby", etc.) | Out of scope; not analysed |

## 6b. Enumeration

**Space definition.** The system is a single fixed-length button sequence, not a
text password. Fields: length = exactly 10 presses (`cmp r1,#10` at `0x0800F614`);
positions 0–9 with fixed single-bit masks from the table above; no checksum, no
variable field, no reserved bits. A "press" is one newly-pressed key mask; because
the test is `press & expected != 0`, any chord whose mask contains the expected
bit is accepted at that position. Of the 1,024 possible 10-button chords, 512
contain a given expected single bit, so the accepted input space is at least
`512^10 ≈ 1.2×10^27` distinct 10-press sequences. The **outcome** space is one bit
(`flag=0/1`); there is exactly one action branch and one table.

**Bounded static negative for other systems.** Only two code sites reference the
progress word `0x03003810` (`0x0800F4E0`, `0x0800F640`/`0x0800F66C` — the same
function; the other two hits at `0x0802A1A8`/`0x0802A1C4` are inside a literal-pool
/data block of plaintext strings, not code). Only one code site writes the flag
(`0x0800F61C`); its other literal hits are the reader at `0x0800E788` and data
blocks. A full 4 MiB scan for runs of ≥4 consecutive `u16` values drawn from the
10 mask values found no second plausible code table (all long runs were repeated
`0x0001` in graphics/audio data). No password alphabet, table of textual codes,
or checksum constant was found. This is a bounded "single button-code system"
result, not "not searched".

**Novel codes (minted here, absent from every published list).** Each was entered
on the real title screen after loading a pristine state; RAM and menu were read
afterwards.

1. **L-shoulder overlay sequence** (adds L to 9 of 10 presses; only the B press
   is plain):
   ```
   L+↑  L+↑  L+↓  L+↓  L+←  L+→  L+←  L+→  B  L+A
   ```
   Result: `flag@0x03004B64 = 0x01`, index 0, main menu shows **Demolition Derby**
   (screenshot `nc_novel_menu.png`). Proves the AND-not-equality semantics: L
   (`0x200`) is unrelated to every expected mask yet does not break the code.

2. **Opposing-direction chord sequence** (uses a chord containing *both*
   directions for the first three presses):
   ```
   (↑+↓) (↑+↓) (↑+↓) ↓ ← → ← → B A
   ```
   Result: `flag = 0x01`, index 0; only 8 distinct button names are used instead
   of 10. Screenshot `rc_novel_vertical_chords.png`.

Both sequences were checked against SuperCheats, cheatingdome, classicemu and
GameHacking.org listings — neither appears.

**Bounds proven by rejection.** From the pristine title state (`flag=0,index=0`):

| Test | Result (`flag`, `index`) | Interpretation |
|---|---|---|
| `↓` substituted for first `↑` (+ rest correct) | `00`, `00` | wrong press resets progress |
| Entire sequence reversed | `00`, `02` | no suffix/order tolerance |
| Only 9 presses (final `A` omitted) | `00`, `09` | length gate `idx==10` not reached |
| Final `A` replaced by `B` | `00`, `00` | last position validated |
| First press `←+→` (lacks expected `↑`) | `00`, `00` | expected bit must be present |
| Broad 8-button chord (`A B L R ↑ ↓ ← →`) ×10 | `00`, `01` | opposing-direction/other-button combination does *not* satisfy every position; bounded negative for that chord |

## 7. Validation evidence

* **Observed** (emulator + savestate RAM):
  * baseline title `flag=0`, title "Press START" yellow; main menu 3 entries.
  * after published Konami code: `flag=1`, "Press START" red, main menu 4 entries
    with "Demolition Derby" (`title.ss1` vs `konami.ss3`, `nc_baseline.png`,
    `t4.png`, `t5.png`).
  * holding Up changes `0x03003878` from `0xFC00` to `0xFC40` and advances
    `0x03003810` from 0 to 1 (`hold_up.ss2`).
  * every menu/race screen walked with `flag=1, index=0` in its savestate
    (`nc_e*.png`, `nc_p*.png`, `nc_t*.png`, `nc_o*.png`, `nc_c*.png`).
  * both novel sequences set `flag=1` and the menu entry appears.
  * all six rejection tests left `flag=0`.
* **Derived** (static disassembly): mask table, validator logic, single action
  branch, flag reader at `0x0800E788`, `0x08061B50`/`0x08061CA0` scene pointers.
* **Inferred**: the `0x50/0x64/0x8C` writes at `0x0800E7D8+` alter racer/AI
  parameters; the exact gameplay parameter name was not traced further.

## 8. Unknowns

* The hint-drawing scene handler at `0x0800F348` is installed via a Thumb pointer
  at `0x08061CA0`, but no retail input path reached it during the full menu walk;
  its trigger (if any) is unknown. It is a scene that renders the in-ROM hint
  text, not an additional code.
* Persistence: the game created a 0-byte `Thunder Alley.sav`, so the flag appears
  to be session-only (re-enter the code each boot); a power-cycle test was not
  performed.
* The precise gameplay meaning of the three `0x50/0x64/0x8C` parameter writes
  was not isolated (observed effect is the unlocked mode).

## 9. Tooling

All scripts were in `/tmp/thunderalley/`:

* `find_table.py`, `dump_table.py`, `scan_codes.py` — literal/pointer/mask scans.
* `stateutil.py`, `ramread.py`, `statediff.py` — mGBA `.ssN` `gbAs` decoder,
  RAM reads and diffs (fallback for the single-client GDB stub, §16.13).
* `keys.py` — XTEST input helper with frame-aligned chords.
* `code_test.py`, `chord_probe.py` — code candidates and rejection tests.
* `gdbdrv.py`, `gdb_watch.py` — attempted GDB stub watcher (stub accepted only a
  single client per launch; breakpoint did not fire, so RAM evidence came from
  savestates).
* `walk.py`, `nav.py` — screen walk with screenshot + savestate per step.

No ROM or copyrighted assets are redistributed; only addresses, hashes,
algorithms and our own generated inputs are published.
