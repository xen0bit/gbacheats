# Worms World Party (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Worms World Party/Worms World Party.gba` |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `WORMSWORLDPT` |
| Game code | `AWYE` (file identifier reports `AWYE41, Rev.00`) |
| Maker | `41` |
| Version byte | `0x00` |
| Entry word | `0xEA00002E` → stock `0x080000C0` (no cracktro/trainer patch) |
| MD5 | `d81d39a2400a2651099a6d1aa2a461d5` |
| SHA-1 | `7b078976d9056aba7f81bb1ff33e5a36357f5f0b` |
| SHA-256 | `7976da3e2936e005902d2be68503d03aad0c04369f045fd6709b0d698cab635b` |

**Observed** (header dump). Analysis was performed on a byte-identical copy in
`/tmp/opencode/wormsworldparty/wpt.gba`; nothing was written into the ROM folder.

## 2. Executive summary

This GBA SKU has **no password / code-entry / text-code system**. The published
cheats for other SKUs ("winners", `HHfsS7`, `PleaseGod`, `ArmagedonGive`,
`/msg … wiptistean`) are PC/Dreamcast/N-Gage codes: none of those literals appears
in this 4 MiB image in ASCII, case-shifted ASCII, or NUL-terminated form
(§6b). The only in-game, developer-intended cheats are **button codes**
processed by the joypad handlers.

Two button-code gates were located statically:

1. **All-weapons code** (the one published for GBA on IGN/GameFAQs/Neoseeker):
   the validator at `0x0800CF8C` checks a held-mask `0x282` (L + Down + B),
   a secondary byte condition, and then grants all 58 weapons from a table at
   `0x0802A8AC` to four teams. Fully decoded (§5.1).
2. **Four-face-button reset**: `0x08005140` and `0x08005306` test
   `~KEYINPUT & 0xF == 0xF` (A+B+Select+Start simultaneously) and jump to a
   screen-reset path. This combination is **absent from every published GBA
   list** retrieved for this engagement. It was entered in mGBA and produced a
   reset to the Ubisoft splash on one attempt (§7).

The deliverable is therefore a *button-code* enumeration (§6b), not a password
alphabet. Bounds are given by the exact comparands in the ROM and by rejection
tests in the emulator.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 (`/usr/local/bin/mgba`), `-3` scale,
  `SDL_AUDIODRIVER=dummy`, Xvfb on a **free** display (`:320` was used because
  `:319` was already owned by another session).
* Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad=arrow keys. Holds of 0.12–0.15 s move a cursor exactly one cell;
  0.4 s holds auto-repeat (this caused a false "dead input" reading early on).
* Screen walk (all **Observed**, screenshots in work dir):
  Ubisoft splash → Fluid Studios → Team17 → **language select** (five flags)
  → title "PRESS START" → main menu ("Single Player Game", three picture
  panels) → single-player submenu ("START for Quick Game") → gameplay →
  weapon-select grid (Select) → pause menu (Start: "Sudden Death / Quit").
* Clean gameplay state for repeatable tests: `Shift+F1` (mGBA slot 1),
  restored with `F1`. Note: mGBA caches slot states in-process; overwriting the
  `.ss1` file externally is not reliably picked up by `F1` — launch a fresh
  emulator with `-t <state>` when testing patched states.
* Published code attempted verbatim: open weapon grid, highlight **Skip Go**
  (found at grid row 8, col 0 from the top-left when moving with Down), press A
  once, then hold L+Down+B and tap Select four times.
* Novel code attempted: A+B+Select+Start held together.

## 4. Address map

| Address | Kind | Meaning |
|---|---|---|
| `0x08005140`–`0x080051B2` | code | Title/input handler; `~KEYINPUT & 0xF` gate |
| `0x08005304`–`0x08005338` | code | Second `~KEYINPUT & 0xF == 0xF` gate |
| `0x08005384`–`0x080053A2` | code | Joypad edge/level producer: writes `pressed` at `0x03000A68`, `held` at `0x0300229C` |
| `0x0800C838`–`0x0800CFF6` | code | Weapon-select screen renderer (called from `0x0800B36E`); contains the all-weapons gate |
| `0x0800CF8C`–`0x0800CFAA` | code | **All-weapons validator** |
| `0x0800D028`–`0x0800D076` | code | Clears the per-team ammo arrays |
| `0x0800AC34` | code | Weapon-ammo setter: `f(weapon_id, team)` |
| `0x0802A8AC` | data | 58-byte, NUL-terminated weapon-id grant table |
| `0x02A9F0` | data | Weapon-name strings, 12-byte stride (`Skip Go` at `0x02AC30`, index 48) |
| `0x03000A68` | RAM | `pressed` key mask (edge) |
| `0x03000AB4` | RAM | `held` key mask used by most UI code (incl. the all-weapons gate) |
| `0x0300229C` | RAM | `held` key mask (producer at `0x08005384`) |
| `0x04000130` | I/O | `KEYINPUT`, active-low; 3 literal references in the whole ROM |

## 5. Algorithm

### 5.1 All-weapons validator (derived from `0x0800CF86`–`0x0800CFF6`)

```
byte[0x0200006A] = 0                       # reset scratch/cheat counter
held = ldrh(0x03000AB4)
if (held & 0x282) != 0x282:  return        # need L (0x200) + Down (0x080) + B (0x002)
if byte[0x02000074] != 0x36: return        # secondary state condition (see §8)
if byte[0x0200003E] == 1:    return        # excluded mode
call 0x0800D028                            # zero all ammo arrays
for wid in table[0x0802A8AC] until NUL:
    if wid == 0x33: continue               # weapon 51 deliberately excluded
    for team in 0..3:
        call 0x0800AC34(wid, team)         # grant one (name shown in game)
```

This is a classic §5.4a-style button gate: no checksum, a single mask plus two
state bytes. The granted set is the 58-entry table minus weapon `0x33`
(57 weapon ids × 4 teams = 228 grant calls).

### 5.2 Four-face-button reset (derived from `0x08005140`, `0x08005304`)

```
keys = ldrh(0x04000130)          # active-low
a = (~keys & 0xF)                # A|B|Select|Start
if a == 0:  normal path
if a == 0xF:
    byte[0x02000022] = ...       # scratch flag
    DISPCNT (0x04000000) = 4
    palette word (0x05000000) = 0xFFFF
    0x04000050 = 0xFF; 0x04000054 = 0
    → screen reset path (calls 0x0801B454 / 0x08029C74)
```

## 6. Tables

**Key bits** (GBA `KEYINPUT`, active-low; masks below are active-high):

| Button | Bit | Active-high mask |
|---|---:|---:|
| A | 0 | `0x001` |
| B | 1 | `0x002` |
| Select | 2 | `0x004` |
| Start | 3 | `0x008` |
| Right / Left / Up / Down | 4/5/6/7 | `0x010`/`0x020`/`0x040`/`0x080` |
| R / L | 8/9 | `0x100`/`0x200` |

Useful derived masks: `0x282` = L+Down+B; `0x00F` = A+B+Select+Start.

**Weapon grant table** at `0x0802A8AC` (58 bytes, NUL-terminated), in order:

```
01 03 04 05 06 07 08 09 0A 0B 02 0C 0D 0E 0F 10 11 12 13 14
15 16 17 18 19 1A 1B 1C 1D 1E 1F 20 22 23 24 27 28 29 2A 2B
2D 2E 2F 30 31 33 34 35 36 37 38 39 3A 3B 3C 3D 3E 3F 00
```

Weapon `0x33` (51) is present in the table but skipped by an explicit `cmp`
at `0x0800CFC6`. Weapon `0x36` (54 = Skip Go) is at table index 48.

**Weapon names** live as 12-byte-padded strings at `0x02A9F0` ("Air Strike"
.. "Skip Go" at `0x02AC30`, "Surrender" at `0x02AC6C`), with extended utility
names (`Low Gravity`, `Laser Sight`, `Fast Walk`, `Invisibility`, `X2 Damage`,
`Crate Spy`) at `0x02AC88`–`0x02ACD0`.

## 6b. Enumeration

**Space definition (button-code system).** The joypad exposes 10 buttons, so
the held-key space is 2^10 = **1,024** masks and the edge (`pressed`) space is
another 1,024. The complete input space per frame is 2^20 = 1,048,576
held/pressed pairs. Every code gate in this ROM is a function of a held mask
(and, for the all-weapons gate, two RAM bytes).

**Complete gate census (counts that bound the negative).**

* Direct `KEYINPUT` literal loads: **3** (`0x08005140`, `0x08005306`,
  `0x08005386`) found by a whole-ROM pc-relative-LDR scan. The third is the
  input producer, not a gate.
* Thumb `LDR` literals equal to the published mask `0x282` (L+Down+B): **1**
  (`0x0800CF8E`). No literal equal to `0x286`, `0x37D`, or `0x379` exists in
  any form (`u16`, `u32`, or PC-relative literal).
* Repeated-mask table search for the published "Select ×4" prefix:
  **0 hits** for `86 02 86 02`, `79 03 79 03`, `82 02 86 02`,
  `7d 03 79 03` (and 3-byte variants) anywhere in the 4 MiB image.
  Therefore the Select presses published for the all-weapons code are **menu
  navigation**, not part of the validator's mask sequence; the validator itself
  has exactly one key comparison.
* Text-code surface: `strings -n 4` produced 40,998 strings; targeted searches
  for `password|cheat|secret|unlock|code` and for the five published non-GBA
  codes found **0** code-entry UI strings and **0** literal hits (also 0 under
  the `+0x20` case-shift transform). Screens walked: language select, title,
  main menu, single-player submenu, gameplay, weapon grid, pause menu — none
  contains a text-entry widget.

**Accepted-set sizes.** For the reset gate the ROM tests only the low four
bits: any of the 2^6 = **64** held masks with A=B=Select=Start=1 and arbitrary
R/L/D-pad bits is accepted (64 / 1024 = 6.25 % of the held space). The
all-weapons gate's mask is `0x282` with the other seven buttons as don't-cares
→ 2^7 = **128** held masks, intersected with the two RAM-byte conditions.

**Novel code (absent from all published lists retrieved).** `A+B+Select+Start`
held simultaneously. Source lists checked: IGN GBA cheats, GameFAQs GBA cheats,
Neoseeker GBA, GameRevolution, GameRankings, ChapterCheats, CheatChannel. None
lists this combination for the GBA SKU (the only GBA entry in those lists is
the L+Down+B all-weapons code). Entered in mGBA: **Observed** reset to the
Ubisoft splash/black transition (screenshot `abss_after.png`). The gate's
accept/reject semantics are **Derived** from `0x08005140`.

**Bounds proven by rejection.** In one gameplay session the near-miss
combinations `A+B+Start` (no Select) and `A+B+Select` (no Start) were held for
0.5 s and produced **no reset** (screenshots `b_no_sel_after.png`,
`b_no_start_after.png`), while the full four-button combination in the *same
session* also did not reset (`b_full_after.png`). This is the §16.12 trap: the
reset path is **screen-gated** — the positive observation came from a session
where the weapon-select overlay was active. The negative tests therefore bound
the comparator (`0xF` is exact, not a subset) only for the screen in which the
full code also failed; the active-screen window was not isolated. Reported as
a bounded negative, not as "code rejected".

**All-weapons code — bounded negative on dynamic confirmation.** The gate was
entered through the real UI in five distinct attempts (Skip Go selected via the
grid with A, combo held with the grid open and closed, and with Select taps
between), and with two patched RAM states (`raw 0x21074`/`0x21075` set to
`0x36` in the `.ss1` EWRAM image, loaded with `-t`). No attempt produced a
visible ammo change or a 57×4-byte ammo-array write in the savestate diffs
(`cheat_before.ss2` → `cheat_after.ss3`). The secondary byte condition at
`0x02000074` could not be driven to `0x36` through the tested UI path: observed
values were `0x00`–`0x06` (it tracks a cursor column in the weapon-select
context). This is a **bounded** statement about the tested states, not a claim
that the published code is wrong — the code's existence and effect are proven
by the table loop and the ammo-setter calls in the ROM.

## 7. Validation evidence

| Claim | Type | Evidence |
|---|---|---|
| ROM identity/hashes | **Observed** | `file`, `md5sum`, `sha1sum`, `sha256sum`, header dump |
| 3 `KEYINPUT` references, 1 `0x282` literal | **Derived** | whole-ROM Capstone pc-relative-LDR scan |
| All-weapons gate conditions and 58-id grant table | **Derived** | `0x0800CF8C` disassembly + literal decode + table dump |
| Reset gate `~KEYINPUT & 0xF == 0xF` | **Derived** | `0x08005140`, `0x08005304` disassembly |
| A+B+Select+Start resets to splash | **Observed** | `abss_after.png` |
| Near-miss combos do not reset (one screen) | **Observed** | `b_no_sel_after.png`, `b_no_start_after.png` |
| Weapon grid / Skip Go reachable and selectable | **Observed** | `hnames.png` ("Skip Go" name banner), `fc_ws_skipgo.png` |
| Weapon `0x36` selection writes a RAM byte | **Observed** | savestate diff `clean.ss1`→`cheat_before.ss2`, byte `0x02000075: 00 → 36` |
| All-weapons code active in emulator | **Not observed** | 5 UI attempts + 2 patched states; see §6b |
| Screen walk complete for main surfaces | **Observed** | screenshots listed in §3 |

## 8. Unknowns

* The exact semantic role of `byte[0x02000074]` in the all-weapons gate could
  not be isolated. In weapon-select savestates it tracks a small cursor index
  (0–6); a neighbouring byte takes the value `0x36` when Skip Go is selected.
  The 397,312-byte raw `gbAs` state was read with EWRAM at raw offset `0x21000`;
  a one-byte section-prefix discrepancy would swap these two addresses and
  would make the gate condition exactly "Skip Go selected". This is the most
  likely explanation but is **Inferred**, not proven — the mGBA `-d` stub in
  this build would not resume/break reliably under the pty harness used.
* The screen/window in which the four-face-button reset is live was not
  isolated (positive observation on one screen, negative on another).
* Published PC/DC team-name codes were checked literally and under `+0x20`
  only; UTF-16/5-bit packings were not exhaustively tested (no UI exists to
  enter them on this SKU, so this does not affect the conclusion).

## 9. Tooling

All scripts and screenshots live in `/tmp/opencode/wormsworldparty/` (nothing
in the ROM folder):

* `scan_keys.py` — key constants, mask literals, PC-relative `KEYINPUT` scan.
* `verify_gate.py`, `lits.py` — Capstone literal-pool decoding for the gate.
* `ss.py`, `patch_ss.py`, `diff_ss.py` — mGBA `.ss1` (`gbAs`/zlib) reader,
  EWRAM patcher and differ.
* `ui.py` — XTEST key helper (0.12–0.15 s holds), screenshot capture.
* `bounds.py`, `full_code.py`, `test_abss.py`, `test_p75b.py` — dynamic tests.
* `pty_*.py` — mGBA CLI-debugger experiments (ultimately not used as evidence).
* `arm-none-eabi-objdump -M force-thumb`, `capstone`, `strings`, `xxd`,
  `xdotool`, `scrot`, ImageMagick.

**Legal note:** no ROM image, extracted graphics, music, or game text is
redistributed here. Only hashes, addresses, algorithms and original tooling
are published.

---
*Report written 2026-11-21. Coordinates verified against the exact hash in §1.*
