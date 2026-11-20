# Tony Hawk's American Sk8land (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Tony Hawk's American Sk8land/Tony Hawk's American Sk8land.gba` |
| Size | 8,388,608 bytes (`0x800000`, 64 Mbit) |
| `file(1)` | Game Boy Advance ROM image: "TH SK8LAND" (BH9E52, Rev.00) |
| Header title (`0xA0`) | `TH SK8LAND` |
| Game code (`0xAC`) | `BH9E` (gamehacking.org's `AH9E` is the **NDS** SKU — different game) |
| Maker (`0xB0`) | `52` |
| Version (`0xBC`) | `0x00` |
| Complement (`0xBD`) | `0x31` |
| Header checksum (`0xBE`) | `0x0000` (rebuilt-header artifact, cf. guide §16.1) |
| Entry branch | `0xEA00002E` (stock) |
| MD5 | `6408c0c1af0e89d5408970cfeb744644` |
| SHA-1 | `9ef930c0dbf6ea2ae3c0da95659ca0e2f4fa7b88` |
| SHA-256 | `5aba14ffb5b7784d109d261ea04ccfd18f6abe692db005a5cb7d2ef5179a6031` |

Observed (header parse, raw bytes). The ROM is the retail image; no cracktro or
appended trainer was found.

## 2. Executive summary

**This GBA SKU has no in-game code system.** There is no password screen, no
code-entry widget, no published or unpublished button-code list, and no reachable
Cheats menu. The only "cheats" in the game are a 14-slot **save-bit unlockable**
set: they are earned by completing Classic mode with N different characters and
are stored as bits in a 32-bit word in EWRAM / the save record. All published
"cheats" for this title are of that kind; every "GameShark / CodeBreaker /
Action Replay" page found during recon is an external cheat device and is out of
scope.

A developer/debug **Cheats menu does exist in the ROM** (title string `"Cheats"`
at `0x080581C4`, constructor at `0x08005C04`, row renderer at `0x08005B10`,
toggle handler at `0x08005B78`) but it is **dead code**: the constructor and its
list builder have zero BL, zero branch, zero 32-bit pointer and zero PC-relative
literal xrefs anywhere in the 8 MiB image, and live mGBA debugger breakpoints on
all four functions never fired while walking every reachable screen (§6b).

The unlockable state itself was characterized and exercised: a synthesized
14-bit mask `0x00003FFF` written to the live cheat-enable word produced a clear
in-game effect (tiny skater + permanently full SPECIAL meter) with a clean
before/after screenshot pair. This is a **debugger-induced RAM state, not a
user-entered code** — labelled as such per guide §16.10. A 32-bit out-of-range
bit (`0x40000000`, bit 30) produced no effect, bounding the field to 14 named
bits.

One web fetch (TCRF) returned a prompt-injection payload (fake "LLM instructions",
an EICAR `key.bin` recipe and a payment demand). It was ignored as data and is
recorded here per guide §16.8.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:315`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
* Keymap (verified in menus): A = `x`, B = `z`, Start = `Return`,
  D-pad = arrow keys, Select = `BackSpace`. Hold ~60 ms; 120 ms double-steps.
* Boot path used repeatedly: wait ~4 s for both splash screens; `Return`;
  `x` × 6 through the story dialogue; `Return` into gameplay; `Return` to pause.
* Screenshots: `scrot` root, crop `720x480+152+144`.
* RAM work: mGBA built-in debugger (`mgba -d`) over a pty. `load 1` restores the
  saved state; `break 0x80152DC` (key reader) halts after a state load; `r/4` and
  `w/4` read/write memory. (The GDB stub on :2345 was unreliable in this
  environment and was abandoned in favour of the built-in debugger.)
* Cheat-effect reproduction: load state 1, halt at `0x080152DC`, read the global
  pointer at `0x02000008` (observed `0x020089DC`), write `0x00003FFF` to
  `[ptr+4]`, delete the breakpoint, continue, start a new Story game and observe
  the skater in the first level.
* Published-code recon: absolutcheats / cheathappens / cheatcc / gamehacking.org
  all agree that the GBA cheats are **progression unlocks**, not typed codes.
  None of the published strings appears literally anywhere in this ROM (see §6b).

## 4. Address map

All addresses are ROM addresses (`file offset = address − 0x08000000`).

| Address | Kind | Meaning |
|---|---|---|
| `0x0805818C` | table | 14 × `u32` pointers to internal cheat names (12 entries) / alias strings |
| `0x080580F8`..`0x08058184` | strings | `stud mode`, `rail balance`, `always special`, `manual balance`, `moon physics`, `lip balance`, `jet pack mode`, `matrix mode`, `turbo mode`, `mini mode`, `nergets` |
| `0x080581C4` | string | `"Cheats"` — title of the dead debug menu |
| `0x080581CC` | string | `"%s: %s"` (row format) |
| `0x080581D4` / `0x080581D8` | strings | `"on"` / `"off"` |
| `0x08005984` | fn | `cheat_name(index)` → `*(0x0805818C + 4*index)` |
| `0x08005994` | fn | `set_enable_bit(struct, index, value)` — clears/sets bit in `[struct+4]` |
| `0x080059AC` | fn | `set_unlock_bit(struct, index)` — sets bit in `[struct+0]`; **one caller only** |
| `0x080059B8` | fn | `test_unlock_bit(struct, index)` — reads bit from `[struct+0]` |
| `0x080059C4` | fn | `any_enable_bits(struct)` — `[struct+4] != 0` |
| `0x08005B10` | fn | dead: render one cheat row (reads `[struct+4] >> index & 1`) |
| `0x08005B78` | fn | dead: toggle handler (key mask `0x30`, calls `0x08005994`) |
| `0x08005BB8` | fn | dead: build cheat-row list |
| `0x08005C04` | fn | dead: construct "Cheats" menu (stores `vptr = 0x087E4B14`) |
| `0x08000C7C` | call site | **sole** call of `0x080059AC` — in the save-load / unlock-apply routine |
| `0x087E4B10` | data | vtable containing `0x08005B79` (toggle handler) |
| `0x02000008` | RAM global | pointer to unlock/enable struct; observed `0x020089DC` |
| `[struct+0]` | RAM `u32` | unlocked/available bitfield |
| `[struct+4]` | RAM `u32` | enabled cheat bitfield — 14 named bits |
| `0x080152DC` | fn | key reader: `ldrh 0x04000130` XOR `0x03FF` → active-high masks |
| `0x080FBB00` | table | 31 localized UI string descriptors (incl. `New Cheat`, `Bypass Goal`) |

## 5. Algorithm / pseudocode

```c
struct CheatState { u32 unlocked; u32 enabled; };   // at *0x02000008

cheat_name(i)  = *(char**)(0x0805818C + 4*i);      // i = 0..13
set_unlock_bit(s,i) { s->unlocked |= 1u<<i; }       // 0x080059AC
set_enable_bit(s,i,v) {                             // 0x08005994
    u32 m = 1u<<i; s->enabled &= ~m; if (v) s->enabled |= m;
}
test_unlock_bit(s,i) = (s->unlocked >> i) & 1;      // 0x080059B8

// 0x08000C68..0x08000C9A — the only writer of s->unlocked:
if (some_classic_completion_flag && index_from_save != -1) {
    cheat = lookup[ index_from_save ];              // table at 0x08057EDC
    if (cheat != 0xFFFFFFFF) {
        set_unlock_bit(s, cheat);
        show_message("New Cheat", cheat_name(cheat));
    }
}
```

The progression gate is a function of save-game completion flags, not of any
controller input. There is no password encoder, no checksum, no character/key
alphabet and no input matcher to reverse. The row renderer and toggle handler
that would let a player turn individual cheats on/off are unreachable (§6b).

## 6. Tables

### 6.1 Cheat slots (internal names, order as stored)

| bit | address of name ptr | internal string | published name (NDS list; GBA list groups 2–4) |
|---:|---|---|---|
| 0 | `0x0805818C` | `stud mode` | Giant Mode (inferred) |
| 1 | `0x08058190` | `rail balance` | Perfect Rail Balance |
| 2 | `0x08058194` | `always special` | Always Special |
| 3 | `0x08058198` | `manual balance` | Perfect Manual Balance |
| 4 | `0x0805819C` | `moon physics` | unknown / cut (inferred) |
| 5 | `0x080581A0` | `lip balance` | Perfect Lip Balance |
| 6 | `0x080581A4` | `jet pack mode` | unknown / cut (inferred) |
| 7 | `0x080581A8` | `matrix mode` | Matrix Mode |
| 8 | `0x080581AC` | `turbo mode` | Turbo Mode |
| 9 | `0x080581B0` | `mini mode` | Tiny Mode |
| 10 | `0x080581B4` | `nergets` | unused alias |
| 11 | `0x080581B8` | `nergets` | unused alias |
| 12 | `0x080581BC` | `nergets` | unused alias |
| 13 | `0x080581C0` | `nergets` | unused alias |

The four `nergets` entries point to the *same* string, so 14 bits encode only
**11 distinct labels** — an alias case like guide §16.4b, not four hidden cheats.
Bit↔published-name mapping for bits 0, 4, 6 and 10–13 is **inferred** from the
internal names and the published unlock table; only bits 2 and 9 were exercised
visually (as part of the all-bits mask).

### 6.2 Published progression thresholds (GBA)

`1` → Create-a-Skater; `2` → lip/manual/rail balance; `3` → Tiny; `4` → Giant;
`5` → Matrix; `6` → First Person Camera; `7` → Replay Cam; `8` → Turbo;
`9` → Always Special; `10` → Paper Tony; `11` → Hoverboard;
`12` → Nearly Always Ribbon; `13` (all chars) → Ninja Skater.
These are **unlock conditions**, not enterable codes. They were not reachable in
the available save state and are recorded as web-recon claims, not observations.

## 6b. Enumeration

### Space definition

* The cheat state is a **32-bit word** (`[struct+4]`) with **14 named bits**.
  Representable enable states: `2^32` as stored, but only `2^14 = 16,384`
  combinations over the named slots; 18 high bits are unassigned.
* There is **no alphabet, no code length, no checksum and no reserved-bit
  validator** — nothing to mint in the password sense.
* The 14 slots collapse to **11 distinct labels** (four `nergets` aliases).
* Published lists describe only **13 cumulative unlock tiers**, i.e. 13 nested
  subsets of the 14 bits, not arbitrary combinations.

### Novel synthesized value (debugger-induced, not a typed code)

* Value `0x00003FFF` (all 14 bits) written to `[0x020089DC+4]` after `load 1`.
* **Not in any published list** — no published source describes a single code
  that turns on all cheats simultaneously; the external AR code that does this
  (`121c6b58 0000ffff`) is a DS cheat-device code, not an in-game GBA input.
* **In-game proof (Observed):** `beforeafter.png` — baseline at left shows a
  normal-size skater and an empty SPECIAL meter; after the write (right) the
  skater is ~1/3 size and the SPECIAL meter is completely filled/yellow. This
  simultaneously exercises the "mini mode"/Tiny and "always special" effects.
* **Labelling:** this was produced with mGBA's debugger `w/4`, because the game
  has no user-facing way to enter it. Per guide §16.10 it is **not** claimed as a
  code the player can type.

### Bounds proven by rejection / non-effect

* Out-of-range bit 30 (`0x40000000` written to the same word) produced **no**
  visible effect (`bp30_c.png`: normal-size skater, empty SPECIAL meter) — the
  14-bit field bound is real, the remaining 18 bits are inert.
* A 12-pattern scan for password/code strings and alphabets
  (`ABCDEFGHIJKLMNOPQRSTUVWXYZ`, `0123456789ABC…`, `BCDFGHJKLMNPQRSTVWXYZ`,
  `PASSWORD`, `PASSCODE`, `Enter Password`, `CODE:`, `Cheat Code`,
  `SECRET CODE`, `UNLOCK CODE`, `1234567890`, lowercase alphabet) returned
  **0 hits** in all 8 MiB.
* Keyword `strings` scan: `password` **0**, `cheat` 2 (one internal title, one
  `New Cheat` UI descriptor), `secret` 2 (a story collectible goal), `debug`
  **0**, `level select` **0**.
* Button-code mask scan (u16 arrays of 4–10 active-high key masks including
  L/R) found 4,472 candidate runs in compressed/bytecode data; **none** is
  referenced by a 32-bit pointer or a PC-relative literal from executable code,
  and no published button sequence exists for this SKU.

### Bounded negative for the "Cheats" menu and any code surface

| Check | Result |
|---|---|
| Screens walked with RAM/screenshot evidence | 16 distinct screens/states (both splash screens, create-a-skater, story dialogue, gameplay, saving overlay, pause + its TRACKS and OPTIONS submenus, main menu + STORY/OPTIONS/SOUND/CLASSIC/HEAD-2-HEAD submenus) |
| Code-entry widgets on those screens | **0** (the only text field is the create-a-skater name, a label, not a validator — cf. §16.2b) |
| Reachable "Cheats" menu entries | **0** |
| `0x08005C04` xrefs: BL / B / 32-bit pointer / PC-relative literal | **0 / 0 / 0 / 0** |
| Same for `0x08005BB8` (row-list builder) | **0 / 0 / 0 / 0** |
| Live breakpoints at `0x08005C04`, `0x08005BB8`, `0x08005B78`, `0x08005B10` | installed and verified with `listb`; **0 hits** across the full 16-screen walk |
| Published password/code lists that appear literally in the ROM | **0** (all recon results are unlock descriptions or external cheat-device codes) |

These counts make "no code system in this SKU" a bounded negative rather than an
unexamined guess. The dead Cheats menu is the "dead code" case of guide §16.3;
the progression unlock is the "save-bit unlock, not a code" case of §16.18.

## 7. Validation evidence

* **Observed** — header/hashes; all 16 screens and menu item counts; the
  14-entry name table bytes; `listb` showing four installed breakpoints and zero
  hits; `[0x02000008] = 0x020089DC`; `[struct+4] = 0` before the write and
  `0x00003FFF` after; the before/after screenshots; the bit-30 non-effect.
* **Derived** — the helper semantics at `0x08005984`–`0x080059C4`; the single
  unlock-writer call site at `0x08000C7C`; zero static xrefs for the dead menu;
  the key-mask reader at `0x080152DC`.
* **Inferred** — bit↔published-name mapping for all bits except 2 and 9; that
  `moon physics` / `jet pack mode` are cut or renamed cheats; that the four
  `nergets` slots are aliases rather than distinct content.

## 8. Unknowns

* Which save-field/threshold selects each of the 14 unlock bits; the save record
  was not fully decoded, so the exact Classic-mode→bit map is not proven.
* Whether the dead Cheats menu was ever reachable in a prototype build.
* The three `nergets` strings beyond the first and the two unnamed dev cheats
  (`moon physics`, `jet pack mode`) have no confirmed retail effect.
* Individual effects of bits 0, 1, 3–8 and 10–13 were not exercised one at a time.

## 9. Tooling

* `strings -t x`, `xxd`, Python `struct` scans (`xref.py`, `lit.py`, `blscan.py`, `allxref.py`).
* `arm-none-eabi-objdump -M force-thumb/force-arm` for all disassembly shown.
* mGBA 0.10.5 with Xvfb `:315` + openbox; `xdotool` XTEST input; `scrot` + ImageMagick crops.
* mGBA built-in CLI debugger over a Python `pty` (`dbg.py`) for `load 1`, `break`,
  `r/4`, `w/4`. Helper scripts: `deadcode2.py`, `walk.py`, `eff2.py`, `eff3.py`,
  `bitprobe.py`. GDB RSP client (`rsp.py`) was written but the stub proved
  unreliable and was not used for conclusions.
* Savestate `gbAs` chunk was decompressed for inspection (397,312-byte state).

## 10. Legal note

No ROM bytes, graphics, audio or game text are redistributed here. Only hashes,
addresses, internal labels, algorithms and original observations are published.
