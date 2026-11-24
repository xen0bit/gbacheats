# Rock n' Roll Racing (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Rock n' Roll Racing/Rock n' Roll Racing.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `RRRACING` |
| Game code | `A4RE` (A = USA, revision 00) |
| Maker code | `7D` |
| Version byte | `0x00` |
| Complement / checksum | `0x72` / `0x0000` (checksum 0 is the normal rebuilt-header artifact; §16.1) |
| Entry word | `0xEA00002E` = stock `b 0x080000C0` — **no cracktro/trainer/patched entry** |
| Embedded GBA headers | 1 (Nintendo-logo scan: single hit at file `0x0`) |
| MD5 | `25a0842e3db8b40eeb39de83285cc13a` |
| SHA-1 | `44be0a6869f3495c23a5770993116ac80b554bac` |
| SHA-256 | `e9ca59436c70e4414ad5d8e486d1e40d1b8bd716dca99d15e58fc51d6fa354aa` |

The image is the retail USA GBA release developed by Mass Media / published by
Blizzard Classic Arcade (per 3rd party cheat indexes game detail), not the SNES/Genesis build
by Silicon & Synapse. This distinction is decisive (§16.11): the widely
published 12-character passwords are for SNES/Genesis, not for this SKU.

---

## 2. Executive summary

**There is exactly one button-code system, with two published unlocks, and no
reachable password system in this GBA build.**

1. **Button codes (real, reachable, verified):**
   * Hold **L + R + Select** and press **Right** at the **driver-select**
     screen → the hidden seventh driver **Olaf** is revealed and selected.
   * Hold **L + R + Select** and press **Right** while **NHO** is highlighted
     at the **planet-select** screen (VS MODE → CHANGE PLANETS) → the hidden
     sixth planet **Inferno** is revealed and selected.
   Both are the two codes published on the 3rd party cheat indexes GBA cheats page; both were
   reproduced in the emulator. The actual trigger is broader than the published
   wording: the driver version works from *any* highlighted driver (pressing
   the combo from Snake jumps straight to Olaf), while the planet version is
   **position-gated** on NHO. These gate semantics are new (§6b).

2. **Password system: present as leftover data, absent as a feature (cut
   feature, §16.3 case 3).** The ROM contains the 32-symbol password alphabet
   at `0x0804CB04`, the `PASSWORD` string at `0x0804CB9E`, and the stale
   SNES-style `NEW GAME\r\rPASSWORD` menu string at `0x0804C4EE`. The GBA main
   menu instead renders `NEW GAME / LOAD GAME / VS. MODE` because progress is
   stored in EEPROM. No screen in the full menu walk has a password entry or
   display, no published password literal occurs in the image, no code
   cross-reference reaches the password strings, and the SNES password matrix
   is not present in any tested encoding. The published 12-character codes are
   therefore **unverifiable in this SKU** and are reported as not applicable.

3. **`Larry` sound test:** the SNES secret was probed on GBA. Toggling Larry off
   then holding A sets RAM byte `0x03000190` to 2 (vs 0/1 for on/off), but no
   visible or RAM state change followed `L`. With `SDL_AUDIODRIVER=dummy` the
   audio result cannot be heard; treated as **unverified on GBA**.

No GameShark/CodeBreaker/Action Replay codes were used or reported.

---

## 3. How to reproduce

* Emulator: `mgba 0.10.5` (SDL), `DISPLAY=:316`, `SDL_AUDIODRIVER=dummy`,
  `-3` scale. Working copy at `/tmp/rocknroll/game.gba`
  (byte-identical MD5 to the target).
* Default mGBA SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
  Select=`BackSpace`, arrows = D-pad. **Hold keys 0.12–0.25 s**: taps shorter
  than ~0.1 s are dropped, holds longer than ~0.2 s double-step in menus
  (measured; §16.2).
* Boot: title screen → Start → `1 PLAYER` → main menu.

**Olaf code:** main menu → `NEW GAME` → difficulty (any) → `SELECT HERO`.
Hold `L`+`R`+`Select`, tap `Right` once, release. The panel changes to
`OLAF / VALHALLA / +1 ACCELERATION, TOP SPEED, CORNERING`.
Published form ("highlight Tarquinn first") also works; the ROM accepts it
from Snake as well.

**Inferno code:** main menu → `VS. MODE` → difficulty → P1 driver → car shop
EXIT → racing menu → `CHANGE PLANETS` → highlight `NHO` → hold `L`+`R`+`Select`,
tap `Right`. Panel changes to `INFERNO / 160 DEGREES / … WATCH OUT FOR LAVA
POOLS.` Pressing the same combo from `CHEM VI` does nothing (normal advance),
which proves the NHO gate.

**RAM evidence:** mGBA `.ss1` savestates were decoded by extracting the PNG
`gbAs` chunk and `zlib.decompress`ing it (397,312 bytes for this 4 MiB ROM).
IWRAM begins at state offset `0x19000`, EWRAM at `0x21000` (§16.13).
`shift+F1`/`shift+F2` wrote the before/after states.

---

## 4. Address map

All file offsets map to ROM addresses as `0x08000000 + file_offset` (single
header, identity mapping).

| Item | File offset | ROM address | Evidence |
|---|---:|---:|---|
| GBA header / entry | `0x000` | `0x08000000` | observed bytes |
| crt0 / ARM boot | `0x0C0` | `0x080000C0` | disassembly |
| Key reader (Thumb, reads `0x04000130`, XOR `0x3FF`, stores held/pressed) | `0x00B88` | `0x08000B88` | derived (objdump + savestate) |
| Big input/sprite renderer `FUN_08000560` | `0x00560` | `0x08000560` | REA/Ghidra decompile |
| Secondary key routine (EWRAM mirror) | `0x70978` | `0x08070978` | derived |
| Text bank (ASCII, NUL-terminated) | `0x4C000`–`0x4D5xx` | `0x0804C000`– | observed |
| UI string pointer table 1 (270 entries) | `0x4B98C` | `0x0804B98C` | decoded |
| UI string pointer table 2 (60+ entries) | `0x4BB00` | `0x0804BB00` | decoded |
| Alphabet string (32 symbols) | `0x4CB04` | `0x0804CB04` | observed |
| `PASSWORD` string | `0x4CB9E` | `0x0804CB9E` | observed |
| Stale `NEW GAME\r\rPASSWORD` string | `0x4C4EE` | `0x0804C4EE` | observed |
| Font / tile-index table | `0x4CC8E` | `0x0804CC8E` | decoded |

**RAM (GBA address → evidence):**

| Address | Meaning | Evidence |
|---|---|---|
| `0x030059C0` (u16) | active-high held keys; reads `0x0304` while L+R+Select held | Observed (savestate) |
| `0x030059C2` (u16) | companion key state written by `0x08000B88` | Derived |
| `0x02023B98` / `0x02023B9A` | EWRAM held/pressed mirror maintained by `0x08070978` | Derived |
| `0x0300018B`, `0x0300018D`, `0x03000194`, `0x03000195` | unlock flags: **0 → 1** when either cheat fires | Observed (savestate diff) |
| `0x030001B0`, `0x03012E8` | driver index (0 = Snake … 6 = Olaf) | Observed (GDB diff, first session) |
| `0x03000190` | Larry option: 0/1 on, 2 while A held after toggling | Observed |
| `0x0300002C` | transient UI state byte, varies across screens (0x00, 0x03, 0x09, 0x0D, 0x10, 0x12) | Observed, semantics uncertain |

---

## 5. Algorithm

**Button-code gate (derived from behaviour + key-state reads):**

```
held  = ~KEYINPUT(0x04000130) & 0x3FF           # stored at 0x030059C0
pressed = held & ~previous                      # 0x030059C2 / 0x02023B9A

if (held == (L|R|SELECT) == 0x304) and (pressed & RIGHT == 0x10):
       if screen == DRIVER_SELECT:
              selection = LAST_DRIVER          # Olaf, index 6
              set flags 0x0300018B/8D/194/195
       elif screen == PLANET_SELECT and selection == NHO (index 4):
              selection = LAST_PLANET          # Inferno, index 5
              set the same flags
```

The driver branch has no position gate; the planet branch requires NHO. No
other action branch, sequence length, or modifier set produced an effect in
the tested space (§6b).

**Password algorithm (documented for SNES/Genesis, NOT wired into this ROM):**
the external JS generator (3rd party cheat indexes) shows a
12×5-bit XOR matrix `defaultBits =
[[1,0,0,1,0],[1,1,1,1,0],[1,0,1,0,0],[1,0,1,0,1],[0,1,1,0,1],[0,1,1,0,0],
[1,0,1,1,1],[1,0,0,1,0],[1,0,1,0,1],[0,1,1,1,0],[1,1,0,0,1],[0,0,0,0,0]]`
and alphabet `BCDFGHJKLMNPQRSTVWXYZ0123456789!` — the same alphabet present in
the GBA text bank. Each of the 12 output symbols is 5 bits; the field bits
(difficulty, money, driver, division, planet, colour, vehicle, armour,
suspension, tyres, engine, three weapon counts) are XORed pairwise into the
60-bit word. I verified that the published codes use this alphabet and that
the matrix bytes are **absent** from the GBA image in byte, u16-LE and u8
encodings. This ROM therefore lacks the decoder; the GBA text bank is a
wholesale leftover from the SNES UI asset set.

---

## 6. Tables

**Published GBA codes (3rd party cheat indexes GBA cheats page, contrib. eli0918):**

| Effect | Input |
|---|---|
| Play as Olaf (Lost Vikings cameo) | Driver select: highlight Tarquinn, L+R+Select, Right |
| Unlock Inferno in VS mode | Planet select: highlight NHO, L+R+Select, Right |

Both verified in the ROM/build and in the emulator. The remaining 3rd party cheat index
entries on that page (drive anywhere, infinite bullets, infinite money,
Inferno/Olaf via 9-press sequences) are explicitly labelled GEN/SNES and do
not apply to this SKU.

**Decoded UI string table 2 (`0x0804BB00`), relevant IDs:**

| Index | String address | Text |
|---:|---:|---|
| 12 | `0x0804C4EE` | `NEW GAME\r\rPASSWORD` (stale) |
| 13 | `0x0804CB04` | password alphabet (32 symbols) |
| 21 | `0x0804CB9E` | `PASSWORD` |
| 37 | `0x0804CC47` | `OLAF` |
| 49–53 | `0x0804C9A0`… | NEW-GAME racing menu: START RACE / BUY EQUIPMENT / ADVANCE A LEVEL / BUY NEW CAR / SET OPTIONS |
| 54–59 | `0x0804C26E`… | PLANET 0–5 descriptions (CHEM VI … INFERNO) |
| 142–146 | `0x0804C9A0`… | VS racing menu: START RACE / VIEW EQUIPMENT / CHANGE PLANETS / SELECT NEW CAR / SET OPTIONS |

Table 1 (`0x0804B98C`) has 270 entries covering all menus, car/part names,
drivers, credits and endings. Full decoded dump: `/tmp/rocknroll/`
analysis notes (regenerated by the script in §9).

**Unlock flag bytes:** `0x0300018B`, `0x0300018D`, `0x03000194`, `0x03000195`
(all 0 before, all 1 after the cheat; identical for Olaf and Inferno paths).

---

## 6b. Enumeration

**Button-code space.** The gate is exact: one held mask (`0x304`) plus one
edge (`0x10`) on two named screens. Enumerated and tested in-game:

| Input | Screen | Result |
|---|---|---|
| L+R+Select + Right | driver select, **Snake** | **Olaf** selected (novel input, see below) |
| L+R+Select + Right | driver select, **Tarquinn** | Olaf (published) |
| L+R+Select + Left | driver select, Snake | rejected — normal wrap to Tarquinn |
| L+R+A + Right | driver select | not a cheat — A confirmed the driver and left the screen |
| L+R+B + Right, L+Select + Right, R+Select + Right | driver select | rejected (no hidden entry) |
| L+R+Select + Up / Down | driver select | rejected |
| L+R+Select + Right | planet select, **Chem VI** | rejected — normal advance to Drakonis |
| L+R+Select + Right | planet select, **NHO** | **Inferno** (published) |
| L+R+Select + Right | planet select, **Inferno** | rejected — wraps to Chem VI; no 7th/8th planet |
| L+R+Select + Right | main menu, options, slot select, car shop | rejected (no debug screen) |

No hidden debug menu, sound test, extra car, extra weapon or glitch planet was
reachable by any tested combination. The two published codes are the complete
reachable developer-intended cheat set for this SKU.

**Novel / unpublished input (§0.2).** The published instruction requires
highlighting Tarquinn first. The ROM instead accepts **L+R+Select+Right from
Snake (driver index 0)** and jumps directly to Olaf — an input sequence that
appears in no published list. It was entered on the real screen
(`/tmp/rocknroll/52_combo_right_from_snake.png`) and RAM-verified by
the flag diff above. The complementary characterization — that the planet
variant is position-gated while the driver variant is global — is also new.

**Bounds proven by rejection.** Wrong modifier (L+R+A, L+R+B, L+Select,
R+Select), wrong direction (Left/Up/Down), wrong screen (main menu/options/
slots/shop), and wrong position (Chem VI/Inferno) all fail with ordinary menu
behaviour rather than a cheat. This pins the accepted set to exactly
`{held == 0x304, pressed & 0x10, screen ∈ {driver, planet}, planet == NHO}`.

**Password space (negative bounded).** Alphabet 32 symbols, length 12 →
`32^12 ≈ 1.15 × 10^18` possible strings for the SNES format. Search space
actually checked in this ROM: (a) literal search for 4 published codes
(`RM20`, `8M2H`, `RS!V`, `XWJ!`) → 0 hits; (b) all 270+60 UI strings decoded —
the only password-related entries are the alphabet, `PASSWORD`, and the stale
`NEW GAME\r\rPASSWORD`; (c) REA/Ghidra xrefs to those three addresses → only
data-table references, zero code references; (d) the `defaultBits` 60-bit
matrix searched in 3 encodings → 0 hits; (e) every reachable screen walked with
screenshots and RAM/state reads → no password entry or display. The negative
is therefore a statement about the whole ROM image, not an untested guess.

---

## 7. Validation evidence

* **Observed** — title/1P-2P/main/difficulty/driver/car-shop/slot-select/
  racing-menu/CHANGE-PLANETS/planet-select/options/pause/race screens
  (screenshots `00_boot.png` … `161_after_inferno.png`); Olaf panel after the
  combo (`16_after_olaf_code.png`, `52_combo_right_from_snake.png`,
  `150_olaf_proof.png`); Inferno panel after the combo
  (`104_inferno_unlocked.png`); savestate diff showing all four flag bytes
  0→1 (`before_unlock.ss1` vs `after_unlock.ss2`); savestate showing
  `0x030059C0 == 0x0304` with L+R+Select held; ISBN-style published-password
  literals absent from the ROM.
* **Derived** — Thumb disassembly of `0x08000B88` (key reader) and
  `0x08070978` (EWRAM key mirror); Ghidra decompilation of `FUN_08000560`;
  pointer-table decoding at `0x0804B98C` / `0x0804BB00`; the gate pseudocode in
  §5 inferred from the rejection matrix in §6b.
* **Inferred** — that the four flag bytes are *unlock flags* rather than a
  render state (they change together on both cheats and persist); that the
  GBA text bank is a direct copy of the SNES UI asset set; the Larry sound
  test's audible result (untestable with dummy audio).

Evidence limitations: mGBA's GDB stub was intermittent in this shared
environment (single-client port conflicts with other users and a shared
config file that another process changed to port 2362); GDB RAM reads from the
first session were cross-checked against savestate reads. The Inferno flag
diff was not re-captured in a later run — the same four flag bytes are
**inferred** to be set by the shared gate.

---

## 8. Unknowns

* Whether any *unreachable* password validator code exists in a compressed or
  otherwise encoded bank — the string/pointer evidence says no, but a byte
  signature search cannot prove absence for an arbitrary encoding.
* Whether the Larry sound test produces distinct audio on GBA (no audio device
  available; `0x03000190 == 2` while A is held is the only trace).
* Exact semantics of `0x0300002C` and of the four unlock flag bytes' readers;
  no xref-level proof of the final consumer was obtained.
* Whether the two hidden drivers/planets were ever intended as a single
  "extended list" feature; only the observable gates are reported.

---

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep -abo`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000
  -M force-thumb` for key routines; Capstone 5.0.7 / Python 3 for literal-pool
  and pointer-table scans.
* REA MCP (Ghidra provider, raw-binary ARM at `0x08000000`) for `xrefs`,
  `resolve_containing_procedure`, `procedure_pseudo_code`; session closed.
* mGBA 0.10.5 under `Xvfb :316` + `openbox`, `xdotool` for input, `scrot` +
  ImageMagick for screenshots; a private `HOME` config kept the GDB port
  isolated from other agents.
* Python helpers in `/tmp/rocknroll/`: `gba.py` (input/capture),
  `gdbh.py` (GDB FIFO driver), `dump.py` (RAM dumps), plus inline savestate
  `gbAs`/zlib decoder used for the flag diffs.
* Web: 3rd party cheat indexes GBA/SNES cheats pages (via search index), 3rd party cheat indexes SNES password generator (algorithm reference only).
* No ROM or extracted assets were redistributed; only hashes, addresses,
  algorithms and original analysis scripts are published.
