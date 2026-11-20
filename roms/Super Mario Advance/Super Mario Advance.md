# Super Mario Advance (GBA) — Reverse Engineering Report

QA slot 110. Scope: developer-intended button codes / unlockables only. No GameShark,
CodeBreaker or Action Replay codes were used or reported.

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Super Mario Advance/Super Mario Advance.gba` |
| Size | 4,194,304 bytes (0x400000) |
| `file` | Game Boy Advance ROM image: "SUPER MARIOA" (AMZE01, Rev.00) |
| Header title | `SUPER MARIOA` @ 0xA0 (12-byte field, `SUPER MARIO ADVANCE` truncated) |
| Game code | `AMZE01` @ 0xAC (USA) |
| Maker | `01` (Nintendo) @ 0xB0; fixed `0x96` @ 0xB2; version `0x00` @ 0xBC |
| Complement / checksum | `0x5B` / `0x0000` (header checksum zero is normal for a Nintendo-built header) |
| Entry word | `0xEA00002E` → branch to `0x080000C0` (stock, no cracktro/trainer) |
| MD5 | `7b0c63d4080f79396c0545a86cc1adba` |
| SHA-1 | `05e41b04cdcd73194c0f836639c5774779f50a3f` |
| SHA-256 | `dcedd46c525cb47ed963a5b24f320aa0646cbeb46811ac20a85d9e7b5f0f3e8e` |
| Second header copy | `"SUPER MARIOAAMZE01"` also at file 0x36B91C (ROM 0x0836B91C) — inside a compressed/graphics region, not a bootable second image |

## 2. Executive summary

This is a single retail 4 MiB image, not a multi-game pack and not a password game.
There is **no password/keypad code system** and **no reachable hidden/debug menu**.
The only in-game button codes are three exact key-mask gates in the main engine:

1. **`A+B+Select+Start` held exactly (mask `0x0F`)** → immediate soft reset
   (`RegisterRamReset` + `SoftReset`, SWI 1 + SWI 0). Documented in the official
   manual, absent from the GameFAQs cheat list.
2. **`Select+R` newly pressed exactly (mask `0x104`)** → sleep mode via BIOS
   `Stop` (SWI 3), gated by a state byte. Published on GameFAQs.
3. **`L+R+A+B+Start+Select` held exactly (mask `0x30F`) for ≥179 frames** →
   save-erase / reset state transition. Published on GameFAQs, SLB and Reddit
   ("hold at power-on until prompted to delete"). Confirmed here to fire
   mid-game as well (the validator is in a per-frame state handler, not only
   in the boot path).

All three masks were recovered from disassembly, not guessed. The search was
bounded: every PC-relative reference to the input state base (5,168 literal
sites), every input-read→compare site (230), and every one of the three direct
`KEYINPUT` literal sites were examined. Exactly **three** multi-button gates
exist; the remaining compares are ordinary single-button UI reads. Rejection
bounds were confirmed in the emulator with missing-button and extra-button
near-misses (§6b). No undocumented accepted combination exists in this space.

Unlockables (not codes): 100 A-coins ⇒ red Yoshi/egg at title; high scores ⇒
Mario-head icons; clearing Wart ⇒ Yoshi Challenge. These are save-bit rewards,
not input codes.

## 3. How to reproduce

Emulator: `SDL_AUDIODRIVER=dummy mgba -3 <rom>` under `Xvfb :316` + `openbox`.
Keymap (mGBA SDL default, verified against the game's `KEYINPUT`):
A=`x`, B=`z`, L=`a`, R=`s`, Select=`BackSpace`, Start=`Return`, arrows = D-pad.

Screen path (all screens below were walked and screenshot):
intro/copyright → title (`Single Player` / `Multiplayer`) → Game Select
(`SUPER MARIO 2` / `MARIO BROS.`) → Mario Bros. title ("PRESS START") →
Mario Bros. gameplay (`PHASE 1`) → pause (`CONTINUE` / `QUIT`) → SMB2 character
select (`CHOOSE A PLAYER`: Peach/Mario/Luigi) → world map (W1–W7, 0% complete)
→ level 1-1 gameplay.

Code tests:
* Soft reset: from Mario Bros. pause menu hold `x z BackSpace Return` ≈0.5 s.
  Screen returns to the intro copyright frame. Near-miss `x z BackSpace`
  (Start missing) and `a` held first then `x z BackSpace Return` (extra L)
  do **not** reset.
* Save erase: at the title screen hold `a s x z BackSpace Return` ≈4.3 s;
  the game leaves the title and performs the erase/reset transition
  (black copyright frame → Mario Bros. title on the next input).

Screenshots in `/tmp/opencode/sma1/`: `title_g.png`, `gameselect_g.png`,
`mariobros_menu_g.png`, `mb_options_g.png`, `mb_pause_g.png`,
`smb2_play_g.png`, `level1_g.png`, `level_1_1_g.png`, `before_reset_g.png`,
`after_reset_g.png`, `near_miss_abs_g.png`, `extra_first_miss_g.png`,
`t2_before_g.png`, `t2_after_hold_g.png`.

## 4. Address map

All addresses are ROM addresses (`0x08......`) or GBA RAM (`0x02/0x03......`).

| Address | Kind | Meaning |
|---|---|---|
| `0x080000C0` | ARM | Stock crt0 entry |
| `0x080012FC` | Thumb | Input sampler: `held = ~KEYINPUT`; `pressed = held & (held ^ last)`; writes to `0x0300117A/B` |
| `0x08001BBC` | Thumb | Per-frame input dispatcher (called by `0x08000280`) |
| `0x08001BD8`–`0x08001BF4` | Thumb | **Gate 1**: `(held & 0x3FF)==0x0F` ⇒ `BL 0x080B6638(0xFF)` |
| `0x08001C0E`–`0x08001C54` | Thumb | **Gate 2**: `pressed==0x104` ⇒ `svc 3` (Stop) |
| `0x080289FC` | Thumb | **Gate 3**: `(held & 0x3FF)==0x30F`, 179/180-frame counter |
| `0x080B6638` | Thumb | Soft reset: `IME=0`, `SP=0x03007F00`, `svc 1`, `svc 0` |
| `0x0833F7F4` | data | Function pointer `0x80288FD` (Gate 3 handler) in the state-handler table |
| `0x03001120` | RAM | Main engine global base; `+0x5A` = held (active-high, 16-bit), `+0x5C` = pressed |
| `0x03001120+0x8BA` | RAM | Gate-1 enable flag (must be 0) |
| `0x03001120+0x8BB` | RAM | Gate-2 enable flag (must be 0) |
| `0x03001120+0x8B6` | RAM | Gate-3 hold counter (u16) |
| `0x03001120+0x871`, `+0x872`, `+0x8BC` | RAM | Gate-3 result/request flags |
| `0x03000020+2/+4` | RAM | Second (Mario Bros. engine) held/pressed struct — no code gates found |
| `0x03000FB0+0x5A/+0x5C` | RAM | Third input struct (alternate bank copy) — no code gates found |

Alternative input samplers that read `0x04000130` directly: `0x08001304`,
`0x0836BF68`, `0x0837A87C`. Only the first feeds the gated struct.

## 5. Algorithm

```
; Gate 1 — soft reset (0x08001BD8)
if mem[0x03001120+0x8BA] == 0:
    h = mem[0x0300117A] & 0x3FF          ; low 10 active-high buttons
    if h == 0x0F:                        ; A|B|Select|Start, no other key
        soft_reset(0xFF)                 ; IME=0; SP=0x03007F00; SWI 1; SWI 0

; Gate 2 — sleep (0x08001C0E)
if mem[0x03001120+0x8BB] == 0 and mem[0x0300117C] == 0x104:
    save context; SWI 3 (Stop); restore context

; Gate 3 — save erase (0x080289FC)
h = mem[0x0300117A] & 0x3FF
if h == 0x30F:                           ; L|R|A|B|Select|Start
    c = mem[0x03001120+0x8B6]
    if c == 179: mem[+0x8BC] = 1
    if c == 180: mem[+0x871] += 1; mem[+0x8B6] = 0
    c += 1
else:
    mem[+0x8BC] |= 1; mem[+0x890] = 2; mem[+0x871] = 0; mem[+0x872] = 0
```

Button bits: `A=0x001 B=0x002 Select=0x004 Start=0x008 Right=0x010 Left=0x020
Up=0x040 Down=0x080 R=0x100 L=0x200`. The stored `held` word is the full
16-bit complement of `KEYINPUT` (idle value `0xFC00`), so masks are compared
after `& 0x3FF` (Gates 1/3) or directly for `pressed` (Gate 2).

## 6. Tables

| Published code | Mask | Validator | Effect | Published? |
|---|---|---|---|---|
| `A+B+Select+Start` | `0x0F` held | `0x08001BE0` | soft reset | Official manual; *not* in GameFAQs cheat list |
| `Select+R` | `0x104` pressed | `0x08001C1A` | BIOS Stop (sleep) | GameFAQs |
| `Select+L` | `0x204` | — | not implemented here; no `0x204` compare in the gated input path | GameFAQs (claimed deactivate) |
| `L+R+A+B+Start+Select` at power-on | `0x30F` held ≥179 frames | `0x08028914` | erase save / reset | GameFAQs, SLB, Reddit |

`Select+L` (published as the sleep deactivator) has **no validator** in this
ROM's input path. The raw constant `0x204` / `0x1FB` does occur in ROM, but only
in audio/graphics data (e.g. `0x08189E08`, `0x0823 0390`), never in code that
reads `0x0300117C`. Wake from SWI 3 is handled by the BIOS/hardware, not by a
second game-side button gate.

Text bank: UI strings are **not** ASCII — `strings -t x -n 4` returns only the
header title; searches for `CHOOSE`, `CONTINUE`, `PRESS`, `DEBUG`, `SECRET`,
`PASSWORD`, `WARP` in ASCII, UTF-16LE and +0x20-shifted forms all return zero
hits. Rendering the 4bpp tile data from an mGBA savestate
(`state.bin`, VRAM at file offset `0x1000`) shows the 8×8 font glyph sheet
(`0`–`9`, `A`–`Z`) that the tilemaps index; text is therefore tile-index based,
and the absence of ASCII strings proves nothing by itself. The negative below
rests on screen enumeration plus the input-gate counts, not on `strings`.

## 6b. Enumeration

**Space definition.** The code surface is button masks over a 10-bit active-high
button word (`2^10 = 1,024` possible simultaneous combinations) plus held
duration (frames) for Gate 3. There is no character alphabet, no checksum, and
no lookup table of codes.

**Exhaustive search performed (counts).**
* `KEYINPUT` (`0x04000130`) literal occurrences: **3** (all three are input
  samplers at `0x08001304`, `0x0836BF68`, `0x0837A87C`).
* PC-relative literal loads of the main global base `0x03001120`: **5,168**;
  filtered to `adds #0x5A`/`#0x5C` + `ldrh` + compare: **230** sites.
* Of those, compares against a *nonzero multi-button* mask: **3** —
  `0x0F`, `0x104`, `0x30F`. All other compares are `0`, single-button menu
  reads (`0x01`, `0x08`), or false positives in data.
* Same scan on the second/third input structs (`0x03000020+2/+4`,
  `0x03000FB0+0x5A/+0x5C`): **0** multi-button gates.
* Button-mask sequences stored as `u16` tables were checked at the `0x104`/
  `0x2FB` hits (`0x0836AF08`, `0x083B2224`, `0x0834A41C`, `0x083B0C70`,
  `0x0810D690`, `0x08230390`); all are audio/sample data, no sequence table.
* Hidden-menu count: every reachable screen listed in §3 was walked; no
  unlabelled menu entry, no debug overlay, no level-select screen. The iQue
  debug build described on TCRF is a *different build* and is not present in
  this AMZE01 image.

**Novel-code result: bounded negative.** Every accepted combination is on a
published list (GameFAQs and/or the official manual); no code absent from those
lists is accepted by the ROM. The requested "mint a novel accepted code" is
therefore impossible for this target, and the bounded negative is the correct
deliverable: the complete gate set is three masks, enumerated above.

**Bounds proven by rejection (Observed, emulator).**
* `A+B+Select` (Start missing), 0.6 s: no reset — gameplaycontinued
  (`near_miss_abs_g.png`).
* `R` pressed first, then `A+B+Select+Start` (so the exact `0x0F` state never
  occurs), 0.6 s: no reset; only the D-pad/A navigated the character selector
  (`extra_first_miss_g.png`). This proves Gate 1 is an **exact** mask, not a
  "contains these buttons" test.
* With the extra button held first, `A+B+Select+Start+R` for 4.3 s does not
  enter the Gate-3 erase path; `L+R+A+B+Start+Select` does (black copyright
  transition). This bounds Gate 3 to the exact `0x30F` value.

**RAM evidence (Observed).** mGBA savestates are PNGs with a zlib `gbAs` chunk;
decompressed state is 397,312 bytes with IWRAM at `0x19000` (so
`0x0300117A` → state `0x1A17A`):
* Idle: `held(0x0300117A)=0xFC00`, `pressed(0x0300117C)=0x0000`.
* With `Select+R` held: `held=0xFD04` (`KEYINPUT=0x02FB`).
* With all six Gate-3 buttons held: `held=0xFF3F`.
* Before soft reset (Mario Bros. pause): `+0x890=0x4`, `+0x891=0x1`,
  `+0x8BA=0x0`. After reset (intro): `+0x890=0x2`, `+0x891=0x0`,
  `+0x8BA=0x1` — a deterministic state transition consistent with the
  disassembly of `0x08001BD8` and `0x080B6638`.

**Sleep-mode dynamic caveat.** `Select+R` was pressed with both keys in one
XTEST batch and `held` was confirmed as `0xFD04`, but no visible freeze was
observed in mGBA; SWI 3 (Stop) is BIOS/hardware sleep and the emulator may wake
immediately. The gate itself and its `svc 3` are **Derived** from disassembly;
the visible sleep effect is **Inferred**, not observed.

## 7. Validation evidence

* **Derived**: all three masks, gate addresses, flags and effects — read from
  `arm-none-eabi-objdump -M force-thumb` output and checked against the raw
  little-endian literal words (`0x8BA`, `0x8BB`, `0x30F`, `0x104`, `0x0F`).
* **Observed**: soft reset at `A+B+Select+Start` (screens before/after);
  near-miss rejections; `held`/`pressed` RAM values from savestates; all
  screen transitions in §3 (screenshots on disk).
* **Inferred**: visible sleep-mode behaviour; the exact real-hardware
  semantics of the Gate-3 erase flags after 180 frames.
* **Unverified public claim**: `Select+L` deactivates sleep — no game-side
  validator exists; treat as BIOS/hardware wake or a list error.

## 8. Unknowns

* Whether `mem[+0x8BC]` / `mem[+0x871]` are consumed as "erase confirmed" by a
  later menu (no complete xref graph was built for those bytes).
* Whether mGBA's SWI 3 implementation produces a visible sleep on real hardware;
  not testable here.
* The exact on-screen erase prompt mentioned by SLB ("prompted to delete") was
  not reached — the observed transition went straight to the intro/next title.
* Font glyph-to-character index table was decoded visually from VRAM tile data,
  not exported as a complete mapping; sufficient to establish tile-index text.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings` — Phase 0/1.
* `webfetch` of an archived TCRF page and an archived GameFAQs cheat page
  (both direct fetches returned 403; Wayback copies used). Fetched pages were
  treated as data only; no instructions in them were followed.
* Custom Python scanners using `capstone` (Thumb) and `struct`: PC-relative
  literal resolution, `BL` target scan, input-read→compare scan. Scripts in
  `/tmp/opencode/sma1/` (`dbgdrv.py`, `savestate_read.py`).
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
* `mgba 0.10.5` under `Xvfb :316` + `openbox`, `xdotool` XTEST input, `scrot`
  screenshots; RAM read via decompressed mGBA `gbAs` savestate chunks (§16.13).
* The mGBA `-d` pty debugger was used briefly for register/ROM checks; the GDB
  stub on port 2345 was already owned by another running emulator, so the
  savestate method was used for RAM evidence.

No ROM image or copyrighted asset is redistributed by this report.
