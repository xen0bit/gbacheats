# Pitfall: The Mayan Adventure (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Pitfall: The Mayan Adventure.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `PITFALL` |
| Game code / maker | `APFE` / `5G` (Interplay EU), version `0x00` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0, no cracktro) |
| Header checksum / complement | `0x0000` / `0xAD` |
| MD5 | `d307133ff4a778517ab0c00b8ca9379a` |
| SHA-1 | `0de39e1cf6b199721069e8750e94abccc2e4b97d` |
| SHA-256 | `c01d7e10ad2227189b62552cf9ceb86453455099dd96a4e52f05f466941dd911` |

**Phase 0 / embedded-header scan:** the full 156-byte Nintendo logo occurs exactly
once, at file offset `0x4` (header base `0x0`). No second header, no appended
trainer, no multiboot stub, no patch/trainer strings in the first 4 KiB. This is
the retail EU build; addresses below apply to this exact image only.

## 2. Executive summary

The game has **one developer-intended button-code system**, entered on the title
screen. The published sequence `L, Select, A, Select, R, A, L, Select` enables a
debug mode: the title displays a level label — actually rendered **`FOREST 0`**
(3rd party cheat indexes say "FOREST 1", which is wrong by one) — a coordinate HUD replaces the
hearts in play, and holding Select + L/R skips levels. The effect is backed by a
single RAM flag at **EWRAM `0x02000350`** (0 = off, 1 = on), verified across nine
savestates.

The accepted set was enumerated dynamically with that flag as an oracle:
**all 72 single-button substitutions of the 8-press core are rejected**, the
7-press prefix is rejected, and extra presses *before* or *after* the core are
tolerated (the flag is sticky). A novel, unpublished sequence —
`Up, Up, L, Select, A, Select, R, A, L, Select` — was accepted in the emulator,
showed `FOREST 0` and set the flag to 1 (§6b).

A second published sequence, `A, L, A, R, A, L, Select, Select, Start`
("Open Lakamul Rain Forest"), starts the game in a visually different blue
jungle area rather than the normal green forest.

There is **no password-entry surface on the title/options/INFO/pause screens**.
The ASCII text bank does contain `PASSWORD` (`0x080870D1`), `CONTINUE`
(`0x0808718F`, `0x080872B5`) and a prompt-looking `[P] < [T] [F] [A] [> [>`
(`0x080872C1`), but the corresponding screen was not reachable from any menu
walked; it is presumably the Game Over/Continue screen. This is recorded as an
unknown, not as a negative claim (§7).

The input matcher is implemented in the game's **script VM**, not as a literal
comparison table in ARM/Thumb: `0x080023A4` is a script *variable getter* whose
VAR `0x4218` is the live key state, and `0x080024A0` is the paired setter. No
contiguous key-mask table was found for either published sequence.

## 3. How to reproduce

Emulator: mGBA under `Xvfb :316`, `SDL_AUDIODRIVER=dummy`, `mgba -3 <rom>`.
Keymap (verified by reading `KEYINPUT` at savestate offset `0x530`):

| GBA | xdotool key |
|---|---|
| A | `x` |
| B | `z` |
| L | `a` |
| R | `s` |
| Start | `Return` |
| Select | `BackSpace` |
| D-pad | arrow keys |

Important UI quirk: **B is the menu-confirm button** on the title screen; A and
Start start the game. Move the hand cursor with the arrows.

Boot path: intro text screens → attract demo → title (`START / OPTIONS / INFO`).
Press Start on the intro text to reach the title quickly. Save a state at the
title (Shift+F1) — every experiment below starts by loading F1.

Menu path:

* Title → arrows + **B** → `OPTIONS`: `DIFFICULTY: NORMAL`, `SOUND: STEREO/MONO`,
  `CONTROLS` (3 entries; a 4th Down wraps to the first). No PASSWORD entry.
* Title → arrows + **B** → `INFO`: collectibles page, weapons page.
* Title → A or Start → level intro banner (`CEIBA JUNGLE`) → gameplay.
* Gameplay → Start → dimmed pause overlay (no text items).

Codes tested (hold each key ~50 ms with ~60 ms gaps):

| Sequence | Where | Result |
|---|---|---|
| `L, Sel, A, Sel, R, A, L, Sel` | title | `FOREST 0`, flag `0x02000350`=1, debug HUD |
| `Up, Up, L, Sel, A, Sel, R, A, L, Sel` (novel) | title | same, flag=1 |
| `L, Sel, B, Sel, R, B, L, Sel` | title | rejected (normal game) |
| `Sel, L, A, R, Sel, A, Sel, L` (reversed) | title | rejected |
| `A, L, A, R, A, L, Sel, Sel, Start` | title | blue jungle start (Lakamul) |
| 7-press prefix | title | rejected |
| 72 single-button substitutions | title | all rejected |

Debug effects after the working code: title label `FOREST 0`; in play the HUD
shows a coordinate pair (e.g. `064 015` / `076 014`) instead of hearts; holding
Select + R/L while in play changes the displayed coordinates and the area.

## 4. Address map

| Address | Kind | Meaning / evidence |
|---|---|---|
| `0x08000000` | ROM | header; single image |
| `0x080023A4` | Thumb func | key/script-variable getter; reads `0x04000130` via literal at `0x080023E8`, builds internal mask, stores/returns VAR `r1 & 0x3FF` |
| `0x080024A0` | Thumb func | paired variable setter (VAR ids `0x2111`, `0x2108`, …) |
| `0x080870D1` | text bank | ASCII `PASSWORD` |
| `0x0808718F`, `0x080872B5` | text bank | `CONTINUE` |
| `0x080872C1` | text bank | `[P] < [T] [F] [A] [> [>` (password-style prompt) |
| `0x080871FA` | text bank | level names begin (`FOREST 1` … `PITFALL`), 12 names through `0x080874B1` |
| `0x02000350` | EWRAM | **debug flag**: 0 normal, 1 after accepted code (Observed, 9 savestates) |
| savestate `0x00530` | state | KEYINPUT halfword (verified: `a`→`0x01FF`, `BackSpace`→`0x03FB`, `x`→`0x03FE`, `s`→`0x02FF`, `Return`→`0x03F7`, `z`→`0x03FD`) |
| savestate `0x19000` / `0x21000` | state | IWRAM / EWRAM image (§16.13 layout) |

## 5. Algorithm

Internal button masks produced by `0x080023A4` from active-high KEYINPUT:

```
A=0x0080  B=0x8000  Select=0x2000  Start=0x1000
R=0x0040  L=0x4000  Right=0x0100  Left=0x0200  Up=0x0800  Down=0x0400
special: Select+R -> 0x0020 ; Select+L -> 0x0010
```

Th pseudocode of the getter (Derived from disassembly):

```
r4 = r1 & 0x3FF                       # variable index
if r1 == 0x4218:                      # special: live key state
    held = (~KEYINPUT) & 0xFFFF
    new  = held & ~VAR[2]             # edge detect
    VAR[2] = held
    mask = remap(held)                # table above
    base[0x614+r4] = mask & 0xFF
    base[0x615+r4] = mask >> 8
return base[0x614+r4]
```

The published button sequence is consumed by script bytecode in this variable
space; the ARM side only supplies the key-state variable. The validator was
therefore characterised dynamically (§6b) rather than by isolating the script
opcodes.

## 6. Tables

Published GBA codes (3rd party cheat indexes via web.archive.org, 3rd party cheat indexes via web.archive.org — all
verified against the ROM/emulator where a literal could be checked):

| Effect | Code | Screen | Verification |
|---|---|---|---|
| Level Skip / Debug Mode | `L, Sel, A, Sel, R, A, L, Sel` | title | Observed: `FOREST 0`, flag=1 |
| 99 of every weapon | hold `Sel + B` after the above | in play | Not visually confirmed in tested window |
| Fly through level | hold `Sel` + D-pad after the above | in play | Not visually confirmed in tested window |
| Open Lakamul Rain Forest | `A, L, A, R, A, L, Sel, Sel, Start` | title/main menu | Observed: different (blue) start area |
| 9 continues | press Start repeatedly | continue screen | Screen not reached |
| Unlimited continues | waste lives on level 1, press B ×3 at continue | continue screen | Screen not reached |

Literal-table searches (all negative, full-ROM, forward and reversed):
`L,Sel,A,...` and `A,L,A,...` as u8 / u16-LE / u16-BE / u32-LE, using both raw
GBA masks and the internal masks above, and as per-byte low/high halves —
0 hits for every variant. This is consistent with a script-VM implementation.

Text encoding: UI labels on the title/options screens are **font/tile-indexed**
(`START`, `OPTIONS`, `INFO` have no ASCII hit anywhere in the ROM); the ASCII
strings at `0x87060`–`0x87800` are a narrative/informational text bank. The
negative "no password screen on title/options/INFO/pause" therefore rests on
screen enumeration (§3), not on the string scan alone.

## 6b. Enumeration

**Space definition.** Input is a sequence of button presses over the 10 GBA
buttons (A, B, L, R, Select, Start, D-pad ×4) on the title screen. The accepted
core has **length 8** with a **single fixed sequence**

```
L  Select  A  Select  R  A  L  Select
```

There is no checksum, no field layout and no lookup table — the system is an
exact-sequence matcher with a sticky enable flag.

**Validator model / oracle.** `EWRAM 0x02000350` is the accept flag. Reimplement
offline as:

```
def accepts(seq): return seq[-8:] == [L,SEL,A,SEL,R,A,L,SEL]   # extra prefix/suffix tolerated
```

Agreement with the ROM: 72/72 single substitutions rejected, 7-press prefix
rejected, all tested extra-prefix/extra-suffix sequences accepted (flag=1).
Two exceptions to the "any prefix" rule are explained by UI side effects: a
leading B or Start starts the game before the code can be entered.

**Novel code (not in any published list).**
`Up, Up, L, Select, A, Select, R, A, L, Select` — two extra Up presses prepended
to the core. Entered from the saved title state: `FOREST 0` appeared on the title
screen (screenshot `NOVEL_code_crop.png`) and the flag at `0x02000350` read `0x01`
from savestate slot 8. This is a distinct, unpublished spelling that the game
accepts, proving the matcher tolerates leading input.

**Bounds proven by rejection.**

* 72/72 single-button substitutions (every position × the other 9 buttons):
  flag stayed 0; e.g. `L,Sel,B,Sel,R,B,L,Sel` fell through to a normal game start
  (hearts HUD, no coordinate display).
* 7-press prefix: flag 0.
* Reversed 8-press sequence: flag 0.
* Lakamul sequence on title: debug flag 0 (it is a different, independent code).

**Completeness statement.** For sequences of length 8 the accepted set is
exactly `{ [L,Sel,A,Sel,R,A,L,Sel] }`, proven by exhaustive single-substitution
(72 tests). Longer sequences are accepted iff their last 8 presses equal the
core (tested for all 10 possible appended buttons and 8 of 10 prepended buttons).

## 7. Validation evidence

* **Observed** — mGBA screenshots: title, `FOREST 0` debug label, OPTIONS (3
  entries), INFO pages, normal gameplay (hearts), debug gameplay (coordinates),
  dimmed pause overlay, blue-jungle start after the Lakamul code. KEYINPUT values
  read from savestates. Debug flag read as 0/1 from decompressed `gbAs` states.
* **Derived** — internal button mask table and script-variable getter/setter at
  `0x080023A4` / `0x080024A0`; single GBA header; absence of literal code tables.
* **Inferred** — the script bytecode implements the exact matcher (the ROM-side
  validator function was not isolated); the `PASSWORD` ASCII string belongs to a
  Game Over/Continue screen.

Published-list provenance: 3rd party cheat indexes GBA cheats (403 direct, recovered via
`web.archive.org/web/2022/...`), 3rd party cheat indexes GBA page (403 direct, recovered via
`web.archive.org/web/20210607173545/...`), plus search-result snippets from 3rd party cheat indexes. No prompt-injection payload was seen in
the fetched pages; one archive fetch returned HTTP 503 and was retried with a
timestamped URL. The "Begin on Level 6, X, A, Y, A, X…" snippet found in search
results is a non-GBA platform entry (the GBA has no X/Y buttons) and was
discarded.

## 8. Unknowns

* The Game Over / Continue screen, and whether the `PASSWORD` string at
  `0x080870D1` is an entry UI there, was not reached — the player could not be
  killed reliably within the session (full-hearts character survived prolonged
  hazard attempts). The two published continue tricks are therefore recorded as
  *untested*, not rejected.
* The `Sel + B` (99 weapons) and `Sel + D-pad` (fly) sub-codes produced no
  visible HUD change in the tested hold windows; they may require a weapon
  switch or a longer hold. Not confirmed, not refuted.
* The exact script-VM opcode sequence that compares the eight key values was
  not isolated; the accept set is established dynamically and exhaustively.
* No save-type/password persistence was examined (no `.sav` was produced).

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo`
  for Phase 0/1.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
  and Capstone 5.0.7 for literal/BL/xref scans.
* mGBA (SDL) under `Xvfb :316` + `openbox`, `xdotool` XTEST input, `scrot`/`import`
  + ImageMagick crops. mGBA's `-d` CLI debugger (with `stdbuf -o0` and a held
  FIFO writer) was used to confirm the key getter/caller; its GDB stub was
  unavailable because port 2345 was held by another session.
* `/tmp/pitfallmayan/ss.py` — PNG `gbAs` zlib decompressor and RAM
  differ (§16.13); `ui.py` — PID-targeted xdotool helper; `dbg.py` — CLI debugger
  FIFO helper.
* Web: `webfetch` + `websearch`, with `web.archive.org` snapshots for 403'd pages.

Legal note: no ROM bytes, graphics, music or game text are redistributed here;
only hashes, addresses, algorithms, and observations are published.
