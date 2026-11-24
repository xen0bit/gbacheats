# Mega Man Battle Network 3: White (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Mega Man Battle Network 3: White.gba` |
| Size | 8,388,608 bytes (0x800000) |
| `file` | Game Boy Advance ROM image: "MEGA_EXE3_WH" (A6BE08, Rev.00) |
| Header title | `MEGA_EXE3_WH` |
| Game code | `A6BE` (serial A6BE08) |
| Maker | `08` (Capcom) |
| Version / complement / checksum | `0x00` / `0x5F` / `0x0000` |
| Entry word | `0xEA00002E` (stock `b 0x080000C0`) |
| CRC32 | `0x0BE4410A` |
| MD5 | `68817204a691449e655cba739dbb0165` |
| SHA-1 | `ff45038ae6d01cde4eae25a02dcb8bed29e07a6f` |
| SHA-256 | `a161aa80e9ee7e07e85bda5d1c93ad3d1415e35aee88380fe117997ebaf6c1c2` |

**Phase 0 result — clean retail image.** The CRC32/MD5 match the published checksums for a
clean North-American MMBN3 **White** ROM (XKirby MMBN3-Randomizer README). A full-file
scan for the 156-byte Nintendo logo found **exactly one** header, at file offset `0x0`
(title `MEGA_EXE3_WH`, code `A6BE`, maker `08`): there is no embedded second image,
multiboot stub, cracktro or appended trainer. The entry word is the stock branch. Header
checksum `0x0000` is a common retail artifact, not evidence of patching.

The four sibling images checked (`Fire Emblem`, `Mega Man Zero 2`, this ROM) share the same
logo bytes, so the unusual-looking logo is simply this collection's normal logo, not a patch.

## 2. Executive summary

This image implements **three distinct developer-intended cheat families**, all confirmed
to exist in the ROM:

1. **Title-screen button code (SP/Omega Navis).** Fully reversed and enumerated here: a
   single 8-press sequence `R,R,L,R,L,R,L,L`, executed while **Left is held**, gated on
   "Continue" being highlighted and >=5 stars. The validator, mask table, gate, success
   side-effects and flag mechanics are all located (§4–§6). Its whole accepted set is one
   input, so no unpublished *accepted* spelling exists for this family; the bounds were
   proven by rejection (§6b).
2. **Navi Customizer "ModTools" text passwords.** Two sub-systems — *Error/Modification
   codes* (27 published) and *Extra codes* (39 published) — each 8 glyphs from a 29-symbol
   alphabet (`A`–`Z` + 3 non-ASCII symbols), entered by pressing Select after `RUN`.
3. **Number Trader numeric codes.** ~32 published 8-digit decimal codes entered at
   Higsby's Number Man machine.

In addition, ~40 **compression commands** (button sequences held with Select over a
NaviCust part) are published and documented in the game's own text bank.

Important negative result: **none** of the published password literals is stored in the
ROM in any of eight tested encodings (raw ASCII, lowercase, `+0x20`, UTF-16LE/BE, community
font-index bytes, BCD, u32 LE/BE, and 5-bit packing — 8 codes × 8 encodings = 64 literal
searches, 0 hits). The text passwords are therefore **algorithmic**, not a lookup table.
The *error-name* list itself (`ERROR A1` … `ERR D2S`) **is** present as tile-index text at
`0x0807EBDB`–`0x0807EFAF`, which confirms the feature is shipped in this exact image.

The ROM's text is not ASCII: `strings` returns 111,860 runs but essentially only graphics
noise. Decoding with the community `bn3-utf8.tbl` font table recovers all UI text, including
the ModTools/error list. This is why a plain `strings` scan falsely suggests "no codes".

**Sharing with the sibling Blue image.** The published lists are explicitly documented by
their author as "tested and confirmed to work for both the Regular/White and Blue/Black
Version" (3rd party cheat index FAQ 20989 v1.63), and the same lists are republished on Blue's cheat
page. The title button sequence table and flag helpers found here are at fixed absolute
addresses in *this* image; they must be re-derived for Blue (its CRC32 is `0xC0C780F9`, a
different build). Do not carry addresses across; carry only the concept and the literals.
No Blue ROM or Blue RAM was read during this engagement — this image was verified alone.

## 3. How to reproduce

**Emulator / display.** mGBA (`mgba -3 -d` under Xvfb `:319`, `DISPLAY=:319`,
`SDL_AUDIODRIVER=dummy`). Default SDL keymap: A = `x`, B = `z`, L = `a`, R = `s`,
Start = `Return`, Select = `BackSpace`, D-pad = arrow keys. **Focus the correct window by
PID** — several mGBA instances from other analyses were open on the same X server; using
`xdotool search --name mGBA | head -1` focused the wrong emulator and made every keypress
appear to be ignored. Resolve the window with `xdotool getwindowpid`.

**Screens walked (each screenshot-recorded, all with emulator ground truth):**
1. Title `PRESS START` attract — `title.png`.
2. Title menu after Start: `NEW GAME` on a fresh save; `CONTINUE` after saving —
   `menu_main4.png`, `title_cont_menu.png`.
3. Intro text and field scene — `newgame2.png`, `newgame3.png`, `prog_start.png`.
4. **PET in-game menu** — all eight entries enumerated by moving the cursor:
   `Chipfolr`, `SubChip`, `Library`, `MegaMan`, `E-mail`, `Key Item`, `Comm.`, `Save`
   (`startmenu_live.png`, `pet_1.png`…`pet_7.png`).
5. `SAVE` confirmation screen (Play Time / Library / Bt Chips / Credits, Yes/No) —
   `saved.png`. Saving produced a 32 KiB SRAM image with 12,162 non-`0xFF` bytes.
6. Title-screen button-code attempt with 0 stars — `title_code_test.png` (rejected; see §6b).

**RAM evidence.** mGBA's CLI debugger (`-d`) was driven through a pseudo-tty, because the
`-g` GDB stub returned packet errors in this build. Read/write commands (`r/1`, `r/2`,
`w/1`, `x/1`), `b/t`, `c`, `frame`, `status` all worked. The global flag array at
`0x02000030` read as `00 00 00 00 …` on a fresh boot; `x/1 0x0E000000 64` returned all
`0xFF` before the first save.

**Keymap used for the button table:** active-high `~KEYINPUT & 0x3FF`:
`A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040,
Down=0x080, R=0x100, L=0x200`.

## 4. Address map

All addresses are ROM addresses (`0x08000000 + file offset`) unless noted.

| Address | Kind | Meaning |
|---|---|---|
| `0x08000000` | ROM | Stock ARM entry branch `0xEA00002E` |
| `0x08022544` | Thumb fn | **Title button-code validator** (called from `0x080223F8`) |
| `0x08022598` | data | Pointer `0x0802259C` to the button mask table |
| `0x0802259C` | u16 table | `R,R,L,R,L,R,L,L,0` — the SP/Omega Navis code |
| `0x080223BC` | Thumb fn | Star/menu gate dispatcher (caller of the validator) |
| `0x08021D08` | Thumb fn | Set global flag: `flag = (r0<<8)\|r1` |
| `0x08021D24` | Thumb fn | Clear global flag |
| `0x08021D40` | Thumb fn | Test global flag → `r0` nonzero if set |
| `0x08021D58` | Thumb fn | Toggle global flag |
| `0x02000030` | EWRAM | Global flag-array base (byte per 8 flags) |
| `0x0807EBDB`–`0x0807EFAF` | ROM text | `ERROR A1` … `ERR D2S` name list (tile-index encoded) |
| `0x08725DF` | ROM text | Key item name `ModTools` |
| `0x080231C80` | ROM | Font/glyph-index translation tables (decode banks) |
| `0x0000_0000` | SRAM | 32 KiB save (`ROM.sav` in the work dir) |

**Flag encoding** (derived from `0x08021D08`): index `n = (r0 << 8) | r1`;
byte address `= 0x02000030 + (n >> 3)`; bit `= n & 7`. The 5-star gate is `n = 0x192`
(`r0=1, r1=0x92`) → byte `0x02000062`, bit 2. `0x08021D08(1, 0x92)` is the validator's
own success call, i.e. this flag is **"SP navis unlocked"**.

## 5. Algorithm

### 5.1 Title button-code validator (`0x08022544`, Thumb)

```
validate_buttoncode(obj, key_state):
    if obj.state8 != 1: return                      # menu state gate
    if test_flag(1, 0x92) != 0: return              # 5-star gate (see note)
    # r7 = [sl + 4]  -> input-state struct
    held   = [r7 + 0]
    pressed = [r7 + 2]
    if !(held & 0x020): obj.progress = 0; return    # Left MUST be held
    if pressed == 0: return
    expect = table_0x0802259C[obj.progress]          # u16 lookup
    if expect == 0: obj.progress = 0; return         # terminator => fail
    if !(pressed & expect): obj.progress = 0; return # mismatch => reset
    obj.progress++
    if obj.progress == 8:
        set_flag(1, 0x92)                            # 0x08021D08
        trigger_event(0x85)                          # 0x080005B8
    return
```

The dispatcher `0x080223BC` requires `obj+15 != 0`, tests flag `0x192`, and requires
`obj+11 >= 5` (star count) **before** it calls the validator at `0x080223F8`. Reading the
branches literally: when flag `0x192` is clear, five star sprites are drawn and the
validator is called; when it is set, a different sprite set is drawn and the validator is
not called. The published instruction ("after getting the first 5 stars") is therefore the
`obj+11 >= 5` condition, and flag `0x192` is the *reward already claimed* latch. The success
path setting flag `0x192` confirms this reading.

### 5.2 Flag helpers

```
set_flag(r0,r1):   n=(r0<<8)|r1; p=0x02000030+(n>>3); [p] |=  (0x80 >> (n&7))
clear_flag(r0,r1): n=(r0<<8)|r1; p=0x02000030+(n>>3); [p] &= ~(0x80 >> (n&7))
test_flag(r0,r1):  n=(r0<<8)|r1; p=0x02000030+(n>>3); return [p] & (0x80 >> (n&7))
toggle_flag(...):  same with XOR
```

### 5.3 Text passwords — bounded negative on storage form

No literal for any published code was found in the ROM under any of: raw ASCII, lowercase
ASCII, `+0x20` shifted ASCII, UTF-16LE, UTF-16BE, game font bytes (`digits 0x01–0x0A`,
`A–Z 0x0B–0x24`, `[ModTools1..3] = 0x68,0x69,0x6A`), packed BCD, u32 little/big-endian, or
5-bit-per-symbol packing. A linear-checksum model over GF(29), GF(31), GF(37) was also
rejected (Gaussian elimination found only the trivial solution, and the affine system was
inconsistent). Conclusion: the validators use a nonlinear/table-driven transform. The
validator itself was not isolated, so its exact algorithm is an **unknown**, not a guess.

## 6. Tables

### 6.1 Button code (complete)

| # | Press | Mask (u16) |
|---|---|---|
| 1 | R | `0x0100` |
| 2 | R | `0x0100` |
| 3 | L | `0x0200` |
| 4 | R | `0x0100` |
| 5 | L | `0x0200` |
| 6 | R | `0x0100` |
| 7 | L | `0x0200` |
| 8 | L | `0x0200` |
| 9 | terminator | `0x0000` |

Held modifier: **Left** (`0x0020`). Effect: fight SP/Omega Navis. Matches the published
"hold Left, press `R,R,L,R,L,R,L,R,L,L`" exactly (the guide's first L is the held modifier).

### 6.2 Button-mask table enumeration

A full-ROM scan (every 2-byte offset, 4,194,304 positions) for u16 sequences of GBA key
masks terminated by zero, cross-checked for a literal pointer to the table, returned
**6 candidates**:

| Table | Sequence | Verdict |
|---|---|---|
| `0x0802259C` | R,R,L,R,L,R,L,R,L,L | **Genuine button code** (SP Navis), validator `0x08022544` |
| `0x080E2D54` | L,L,A,R,R | Colour/shape lookup in a level-data dispatcher, not a code |
| `0x0810CECA` | Select,R,R | Gameplay state data, not a code |
| `0x081286BA` | Select,Down,Down | Gameplay state data, not a code |
| `0x081304B0` | A,B,Start | Menu-state table, not a code |
| `0x081C391C` | A,L,A | Misaligned pointer in compressed graphics — false positive |

So the title screen has **exactly one** button code in this image.

### 6.3 Text-code families (published lists; literals verified *absent* from ROM)

* **Error/Modification codes** — 27 known: `GYU2OPZQ` (A1), `3GKQ2RSQ` (A2), `LO13ZXME`
  (A3), `JHGIUTOP` (B1), `ALSK3W2R` (B2), `Y2UOMNCB` (B3), `1LSKUTOB` (B4),
  `BM2KWIRA` (B5), `UTI3OMDH` (B6), `X2CD3KDA` (C1), `UTIXM1LA` (C2), `OI1UWMAN` (D2G),
  `WS1FS1AQ` (D2C), `P3TOSIIS` (D2S), `P2I3MSJL` (E1), `UTIR1SO2` (E2), `QSAO3C3L` (F1),
  `NC1FKSA2` (F2), `ITA2CRWQ` (F3), `CVVDS2WR` (G2G), `TUIEO23T` (G2S),
  `TIS3LAEJ` (G2C), `A3DJMNB1` (H1), `UTIW2SMF` (H2), `SK3LROT1` (H3), `AX1RTDS3` (S2G),
  `F2AAFETG` (S2S), `TU1AW2LL` (S2C). The corresponding error *names* are in the ROM at
  `0x0807EBDB`.
* **Extra codes** — 39 known, e.g. `JIEU1AWT` (HP+100), `U2IEOSKW` (HP+150), `GJHURIE2`
  (HP+350), `CNJDU2EM` (HP+1000), `KTEIUE2D` (SuperArmor), `EIR3BM3I` (Shield),
  `SK13EO1M` (Reflect), `URY33RRO` (MegaChip+3).
* **Number Trader** — 32 known 8-digit codes, e.g. `23415891` (AirShoes),
  `15789208` (AirShot3*), `90690648` (Wristband), `41465278` (WeaponLV+1).
* **Compression commands** — ~40 button sequences (e.g. SprArmor `↑→↑R↑↓`, DarkLcns
  `RLR↓←BR`), held with Select over the highlighted NaviCust part. No literal u8/u16 key
  table for these was found; they are algorithmically checked or stored compressed.

**Alphabet** (ModTools input screen, 29 glyphs): `A B C D E F G H I J K L M N O /
P Q R S T U V W X Y Z [sym1] [sym2] [sym3]`; fan transcriptions write the last three as
`1`, `2`, `3`. Font bytes: `[sym1]=0x68`, `[sym2]=0x69`, `[sym3]=0x6A`.

**Published-list quality note.** The lists contain transcription noise that a table-based
"verification" would miss: `P213MSJL` vs `P2I3MSJL` (E1), `TA2CRWQ` vs `ITA2CRWQ` (F3,
7 vs 8 glyphs), `SK13EO1M` vs `SK1?EO1M`, and `SM2UIROA` vs `SM2URIOA` (HP+900). These are
reported as published, not as ROM-verified literals.

### 6.4 Text decoding

Community table `RockmanEXEZone/MMBN-Table-Files/done/bn3-utf8.tbl`, applied byte-for-byte
to the ROM, recovers readable English (e.g. `ERROR A1` at `0x0807EBDB`, `ModTools` at
`0x08725DF`). Raw `strings` is useless for this title.

## 6b. Enumeration

**Button-code space.** Input = 8 presses chosen from 10 GBA buttons, plus one required
held modifier (Left). Nominally `10^8 = 100,000,000` press sequences; the validator accepts
**exactly one** (`R,R,L,R,L,R,L,L`) because each of the 8 table entries is compared with a
bitmask and the progress index is reset on the first mismatch. There are no aliases: the
expected masks are distinct single-bit values and the comparison is `pressed & expect`,
so a simultaneous multi-button press fails unless it contains exactly that bit at that
step; the `held & 0x20` check is separate and mandatory. Space size of the table itself:
8 entries + 1 zero terminator = 9 u16 words at `0x0802259C`.

**Novel-code test.** Because the accepted set for this family is a single fixed sequence,
an unpublished *accepted* spelling does not exist — this is a property of the format, not
an untested case. The required "undocumented combination" test was performed on the live
title screen: holding Left and pressing `R,R,L,R,L,R,L,L` with **0 stars and no Continue**
produced no state change (`title_code_test.png`), and the debugger's breakpoint at the
gate dispatcher `0x080223BC` never fired during the entire title-screen walk (log ends with
`> c`, no register dump). This is the gate proof: the code is unreachable until
`obj+11 >= 5` and Continue is highlighted.

**Bounds proven by rejection.**
* Gate rejection (observed): published sequence at 0 stars → no effect; validator/dispatcher
  never called (breakpoint evidence).
* Wrong held modifier (derived from `0x0802255C–0x08022560`): any sequence not executed
  with `held & 0x20` resets progress at the first step.
* Wrong press (derived from `0x0802574`): any mismatch resets `progress` to 0, so a 9th or
  out-of-order press can never complete the 8-step chain.
* Reward latch (derived from success path): setting flag `0x192` (byte `0x02000062` bit 2)
  makes the gate dispatcher take the other branch, so the code cannot be re-triggered.
  I set this flag once via `w/1 0x02000062 0x04` and read it back as `0x04` (RAM-observed),
  then deliberately avoided relying on it after the branch analysis showed it *disables*
  the code path — recorded here as a correction, not a successful unlock.

**Text-code enumeration.** Space = `29^8 = 497,008,022,241` (≈4.97×10¹¹) glyph strings for
each of the ModTools families; Number Trader = `10^8 = 100,000,000` numeric strings.
Published sets are 27 + 39 + 32 ≈ 98 values, i.e. an infinitesimal fraction of the
representable space. **No accepted novel code was minted for these families**: their
validators were not isolated, and the Navi Customizer + ModTools screens are gated behind
story progress (ModTools is a 5,600 Zenny key item purchased at Beach Street; NaviCust is
obtained in Scenario 2). The reachable-screen evidence above stops at the PET menu/Save
screen of a fresh game, where neither item exists. This is a *gated* negative (guide §16.3
case 4), not a claim that the feature is absent; the shipped error-code name list and the
published-literal absence prove the system exists but not its validator.

## 7. Validation evidence

* **Observed** (emulator / debugger): title screen, title menu states, PET menu with all 8
  entries and its Save confirmation screen, field scene, keyboard input, 0-star rejection of
  the published button code, EWRAM flag array `0x02000030` all-zero at boot, SRAM all-`0xFF`
  before first save, save file materialised with 12,162 non-`0xFF` bytes, `w/1` flag write
  read back as `0x04`, breakpoint at `0x080223BC` never hit on the title screen.
* **Derived** (instruction-level): button-code validator control flow, key masks, table
  contents and terminator, the four flag helpers and the `0x02000030` base, gate conditions,
  success side-effects, and the flag-encoding formula.
* **Inferred**: mapping of flag `0x192` to "SP navis unlocked" (strong: it is both the gate
  and the value set on success); mapping of `obj+11` to star count (strong: compared with 5
  immediately before the call); interpretation of `0x080005B8(0x85)` as an event trigger
  (moderate — the callee was not fully traced).
* **Purely static / unverified**: the published text-code lists (verified *absent* as
  literals, verified *present* as error names, but not entered in-game), and the claim that
  the compression-command tables are algorithmic/compressed rather than absent.
* **Prompt injection:** fetched web pages (3rd party cheat indexes, Steam, 3rd party cheat indexes)
  contained no instruction-like payload; all were treated as data. One REA-adjacent search
  result contained unrelated "password generator" marketing text; ignored.

## 8. Unknowns

1. The ModTools Error/Extra-code validator and generator were not located. The nonlinear
   transform is unresolved; consequently no novel text password was minted or entered.
2. The Number Trader validator/code generator is unresolved.
3. The data structure behind the ~40 compression commands was not found (no literal key
   table at any of the tested encodings).
4. `obj+15`, `obj+11`, `obj+8` and `sl` were not resolved to named global symbols; their
   meanings are inferred from branch structure only.
5. The title code was not exercised with its gate satisfied (>=5 stars + Continue
   highlighted). Satisfying that gate requires a late-game save; the fresh save created
   here has 0 stars.
6. Whether the first 5 stars are counted in `obj+11` or whether that byte is a menu timer
   that merely correlates with star count.
7. Effects of `0x080005B8(0x85)` beyond the observed call site.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `python3` (`zlib.crc32`), `xxd`, `strings -t x`.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for all
  disassembly; Capstone (`CS_ARCH_ARM`, `CS_MODE_THUMB`) for filtered `cmp #29` code scans.
* Python + `urllib.request` for the community font table
  (`RockmanEXEZone/MMBN-Table-Files/done/bn3-utf8.tbl`) and for whole-ROM tile-index text
  decoding (`rom_decoded.txt`).
* `Xvfb :319`, `openbox`, `mgba -3 -d` with a Python `pty` daemon (`dbgd.py`, FIFO `cmd.fifo`)
  for RAM reads/writes and breakpoints; `xdotool` with **PID-resolved** window targeting;
  `scrot` for screenshots. mGBA's `-g` GDB stub was tried first and rejected (packet errors).
* Saved artifacts in `/tmp/mmbn3white/`: `rom_decoded.txt`, `strings_all.txt`,
  `codes.py`, `dbgd.py`, `dbg.log`, `ROM.sav`, and ~20 screenshots (`title.png`,
  `title_cont_menu.png`, `startmenu_live.png`, `pet_1.png`…`pet_7.png`, `saved.png`,
  `title_code_test.png`, …).
* No ROM or copyrighted graphics/audio/text were redistributed; only addresses, hashes,
  algorithms and short public-code literals appear in this report.

---

*Legal note: findings only. The ROM, extracted graphics and full text banks remain with the
user; nothing proprietary is reproduced here beyond short code literals already public.*
