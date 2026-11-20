# Tony Hawk's Underground (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Tony Hawk's Underground.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| Header title | `THUGTHUGTHUG` (12 bytes at 0xA0) |
| Game code / maker | `BTOE` / `52` (Activision, USA) |
| Version | 0x00 (Rev. 00) |
| `file` classification | `Game Boy Advance ROM image: "THUGTHUGTHUG" (BTOE52, Rev.00)` |
| Entry word | `0xEA00002E` → `b 0x080000C0` — stock crt0, not a cracktro |
| Fixed `0x96` @ 0xB2 | present; complement byte 0x18; header checksum 0x0000 |
| MD5 | `21eb6a30820e14768e0c20aeeffbf587` |
| SHA-1 | `ec66e125147a3271e76e65737f0927efe9a4b7fe` |
| SHA-256 | `9de037cd15f2733cc146fdf40d009e405c8ca2bba68a5dba9ed93cbf30b21d90` |

Engine strings confirm the Vicarious Visions GBA build (`Developed By Vicarious Visions, Inc.` at
file 0x48F28; audio banner `Shin'en Multimedia. Code: B.Wodok` at file 0x7F2C16). This is the
standalone BTOE52 SKU, not the 2-in-1 pack; no other ROM image was analysed.

## 2. Executive summary

**There is no typed password / cheat-code validator in this GBA image.** The developer-intended
cheat surface is the OPTIONS → CHEATS screen, a **15-row toggle list** whose entries unlock only
by completing 100% of Arcade Mode goals with specific pro skaters. The entire mechanism was
recovered: 16 cheat-name strings (file 0x48C74), an 18-slot pointer table (file 0x48D48), the
helper functions `CheatName` / `CheatUnlock` / `CheatIsUnlocked` / `CheatSetActive`
(0x08004B6C … 0x08004BA0), the single goal-checking unlock caller (0x08000A60–0x08000BD6), and
the skater→cheat map (0x08048A08) that gates it. The two state bitmasks live in EWRAM at
**0x0200D364** (unlocked) and **0x0200D368** (active), reached through the global pointer slot
**0x02000008** — both read as 0x00000000 on a fresh save.

A **16th cheat, `nergets`, exists in the name table but is never shown in the menu and has no
skater mapping**: the map's value set over all 18 entries is `{0,1,…,14,0xFFFFFFFF}`, so index 15
cannot be produced by the only unlock caller. This is an arithmetic proof that no in-game input
can reach it (guide §16.3b). It also appears in no published list.

The GBA-specific published **button code** ("Skip Tutorial — hold R, `← ↓ START START → ↑ ↑ L ↓`")
was entered at the main menu in the emulator: it moved the menu cursor but produced **no unlock,
no effect and no cheat-bit change** (savestate diff). Exhaustive searches found no mask table or
comparison chain for it. It is recorded as *published but unverified on this revision*, not as a
working code and not as a proof that the claim is false.

Console cheat passwords (`getitup`, `keepitsteady`, `letitslide`, `rearrider`, `NOOO!!`, `digivid`)
belong to the GC/PS2/Xbox/PC SKUs (guide §16.11). None occurs anywhere in this 8 MiB image in any
of eight encodings.

**Finding: bounded negative for a code-entry surface; high confidence.** The cheat system itself
is fully enumerated (§6b).

## 3. How to reproduce

* mGBA 0.10.5 under Xvfb `:317` + openbox, `SDL_AUDIODRIVER=dummy`, `mgba -3 game.gba`.
  The ROM was copied to `/tmp/opencode/thug/game.gba` (identical MD5) so emulator artifacts never
  touch the ROM folder.
* Keymap (mGBA SDL defaults, verified against menus): A=`x`, B=`z`, L=`a`, R=`s`,
  Start=`Return`, Select=`BackSpace`, D-pad=arrow keys. Holds of 60–150 ms work; menu transitions
  need ~1–2 s before the next input is accepted.
* Boot path (all screens walked): Vicarious Visions splash → Activision splash → story
  narration (tap A) → **ENTER NAME** (Create-a-Skater keyboard) → **CHANGE OUTFIT** → more story
  → story tutorial gameplay → **PAUSED** menu (`CONTINUE / CHANGE LEVEL / SKATER PROGRESSION /
  OPTIONS / SKATE SHOP`).
* To reach CHEATS from a fresh boot: finish the short tutorial dialogue (A to advance, Start to
  pause), pause → `CHANGE LEVEL` → `SKATE SHOP` → B → main menu `T.H.U.G.` (six rows: STORY,
  ARCADE, FREE SKATE, HEAD-2-HEAD, SKATE SHOP, OPTIONS) → `OPTIONS` (seven rows: SOUND, CONTROLS,
  BLOOD LEVEL, DIFFICULTY, DELETE GAME, CREDITS, **CHEATS** — the last two are below the initial
  viewport, press Down 5×) → A.
* CHEATS screen: 15 rows, all `OFF` on a fresh save. Down scrolls; after 15 Downs the selection
  wraps to row 0 — there is no 16th row. Pressing A on `STUD MODE` leaves it `OFF`.
* In-game PAUSED → OPTIONS contains only `SOUND` and `SLEEP`; CHEATS is main-menu only.
* Published code test: at the main menu, hold `s` (R) and tap `Left Down Return Return Right Up Up
  a Down` (the `a` is the L shoulder). Captured `after_published_code.png`; saved savestates
  `game.ss3` (before) and `game.ss4` (after) and decompressed their `gbAs` chunks.
* Savestate RAM reads: mGBA `.ssN` are PNG files with a zlib-compressed `gbAs` chunk; decompressed
  size 0x61000. EWRAM begins at raw offset `0x21000`, IWRAM at `0x19000`. See §9.

## 4. Address map

| Item | ROM address (file offset) | Evidence |
|---|---|---|
| crt0 / entry branch | `0x08000000` (`0x00000000`) | Derived (header bytes) |
| Cheat name table, 16 × 16-byte NUL strings | `0x08048C74`–`0x08048D40` (`0x48C74`–`0x48D40`) | Derived (ASCII bytes) |
| Cheat pointer table, 18 × u32 (16 unique + 2 dups) | `0x08048D48` (`0x48D48`) | Derived (literal-pointer scan) |
| UI string `Cheats` | `0x08048D90` (`0x48D90`) | Derived (ASCII + literal at 0x08004E28) |
| UI string `New Cheat` | `0x080489FC` (`0x489FC`) | Derived (ASCII + literal at 0x08000BE8) |
| UI string `All Goals Completed` | `0x080489DC` (`0x489DC`) | Derived (ASCII + literal at 0x08000BD8) |
| `CheatName(i)` — returns pointer table `[i]` | `0x08004B6C` | Derived (Thumb) |
| `CheatSetActive(struct,i,on)` — set/clear bit `i` of `[struct+4]` | `0x08004B7C` | Derived (Thumb) |
| `CheatUnlock(struct,i)` — set bit `i` of `[struct+0]` | `0x08004B94` | Derived (Thumb; **1 caller**) |
| `CheatIsUnlocked(struct,i)` — test bit `i` of `[struct+0]` | `0x08004BA0` | Derived (Thumb) |
| `CheatNoActive()` — 1 if `[struct+4]==0` | `0x08004BAC` | Derived (Thumb; 0 BL callers) |
| Cheats-menu builder, rows 0..14 | `0x08004BF8`, loop bound `0x08004D3A` (`cmp r7,#14`) | Derived (Thumb) |
| Goal-check → cheat-unlock routine | `0x08000A60`–`0x08000BD6` | Derived (Thumb) |
| Skater→cheat index map, 18 × u32 | `0x08048A08` (`0x48A08`) | Derived (literal at 0x08000BDC) |
| Name-entry alphabet `abcdefghijklm`/`nopqrstuvwxyz`/`0123456789` | `0x0804DD00`–`0x0804DD29` | Derived (ASCII + screenshot) |
| KEYINPUT reader (`KEYINPUT ^ 0x3FF`, active-high) | `0x08011D74` (literals at `0x08011D80`/`0x08011D84`) | Derived (Thumb) |

| Item | RAM address | Evidence |
|---|---|---|
| Global pointer slot → cheat struct | `0x02000008` = `0x0200D364` | **Observed** (savestate `game.ss1`) |
| Cheat unlock bitmask (16 bits used) | `0x0200D364` = `0x00000000` fresh | **Observed** (savestate) |
| Cheat active bitmask (16 bits used) | `0x0200D368` = `0x00000000` fresh | **Observed** (savestate) |
| KEYINPUT | `0x04000130` (active low, 0x03FF idle) | Derived |

A published CodeBreaker *device* code (`8200D364 FFFF`) corroborates the unlock-mask address;
device codes are out of scope and were used only as an address hint (guide §16.20).

## 5. Algorithm

There is no validator to reimplement. The cheat model is:

```
cheat_names[i]  = *(u32*)(0x08048D48 + 4*i)        // i = 0..17, 16 unique names
unlock_mask     = *(u32*)0x0200D364                // via slot 0x02000008
active_mask     = *(u32*)0x0200D368

CheatUnlock(i):    unlock_mask |=  (1 << i)        // only caller: goal-check routine
CheatIsUnlocked(i): return (unlock_mask >> i) & 1
CheatSetActive(i,v): active_mask = (active_mask & ~(1<<i)) | (v ? 1<<i : 0)
```

Goal-check routine at `0x08000A60`:

```
skater = GetCurrentSkater()            // 0x0800C294 -> 0x0800465C
cheat_i = *(u32*)(0x08048A08 + 4*skater)
completed = all goals in goal table complete for this skater
if (completed && cheat_i != 0xFFFFFFFF):
    CheatUnlock(cheat_i)
    show_toast("New Cheat")
    show_toast(CheatName(cheat_i))
```

The CHEATS menu builder draws exactly rows `0..14`; it tests `CheatIsUnlocked(i)` per row but the
row count is a constant loop bound, so locking/unlocking changes only the ON/OFF state, not the
row set. A direct A-press on a locked row produces no visible effect; both masks stay 0
(observed). Whether a later gameplay gate also requires `CheatIsUnlocked` was not isolated.

## 6. Tables

### 6.1 Cheat names (pointer table 0x08048D48; strings at 0x08048C74)

| Index | String ROM address | Name | Published unlock (GameFAQs / cheatcodes.com) |
|---:|---|---|---|
| 0 | 0x08048C74 | stud mode | 100% Arcade, Tony Hawk |
| 1 | 0x08048C80 | rail balance | 100% Arcade, Bob Burnquist |
| 2 | 0x08048C90 | always special | 100% Arcade, Steve Caballero |
| 3 | 0x08048CA0 | manual balance | 100% Arcade, Kareem Campbell |
| 4 | 0x08048CB0 | moon physics | 100% Arcade, Rune Glifberg |
| 5 | 0x08048CC0 | lip balance | 100% Arcade, Eric Koston |
| 6 | 0x08048CCC | jet pack mode | 100% Arcade, Bucky Lasek |
| 7 | 0x08048CDC | matrix mode | 100% Arcade, Bam Margera |
| 8 | 0x08048CE8 | turbo mode | 100% Arcade, Rodney Mullen |
| 9 | 0x08048CF4 | eclipse | 100% Arcade, Chad Muska |
| 10 | 0x08048CFC | crazy lights | 100% Arcade, Andrew Reynolds |
| 11 | 0x08048D0C | mini mode | 100% Arcade, Geoff Rowley |
| 12 | 0x08048D18 | No damage | 100% Arcade, Elissa Steamer |
| 13 | 0x08048D24 | Monkey mode | 100% Arcade, Jamie Thomas |
| 14 | 0x08048D30 | Programmer Art | published: any of Paul Rodriguez / Arto Saari / Mike Vallely |
| 15 | 0x08048D40 | **nergets** | **not in any published list; no unlocker** |

Pointer slots 16 and 17 (`0x08048D88`, `0x08048D8C`) duplicate the `nergets` pointer.

### 6.2 Skater→cheat map at 0x08048A08 (18 u32 values)

`[0,1,2,3,4,5,6,7,8,9,10,11,12,13,0xFFFFFFFF,0xFFFFFFFF,14,0]`

Two skater slots (14, 15) map to the sentinel `-1` and unlock nothing; only slot 16 maps to cheat
14. The published claim that any of three skaters unlocks Programmer Art is therefore **wrong for
this SKU** (guide §16.7).

### 6.3 Name-entry alphabet (0x0804DD00)

`abcdefghijklm` / `nopqrstuvwxyz` / `0123456789` — 36 symbols, rendered as capitals, plus
backspace and accept controls (38 on-screen cells). Consumed by the Create-a-Skater name field;
no comparison constant or validator reads this buffer (guide §16.2b).

## 6b. Enumeration

**Space definition.** There is no alphabet-driven code space. The cheat state is two 32-bit
bitmasks in EWRAM, of which 16 bits each are meaningful: **2^16 unlock states × 2^16 active states
= 2^32 representable configurations**, but the reachable unlock set is only the 15 values produced
by the skater map. The 16th name (`nergets`, index 15) is representable as a bit but **unreachable**:
the map's value set over all 18 entries is `{0…14, 0xFFFFFFFF}` and the unlock routine explicitly
skips `0xFFFFFFFF`. No in-game action, password or button sequence in the analysed surface can set
bit 15. The on-screen CHEATS list has 15 rows; 15 Downs wraps to row 0 (observed).

**Novel code.** Not applicable — there is no validator to mint a code for. Per guide §0.2 item 5,
the negative is proven by counts and a gate-domain proof instead:

| Search | Space checked | Hits |
|---|---|---:|
| Published console codes (17 values) × 8 encodings (ASCII, upper, lower, UTF-16LE/BE, UTF-32LE, ±0x20) | 136 whole-ROM scans, 8,388,608 bytes each (≈1.14×10⁹ byte comparisons) | **0** |
| Published GBA Skip Tutorial sequence in 154 encodings (active-high/low masks, 4 button-index maps, u8/u16LE/u16BE/u32LE/u32BE, forward/reversed, prefixes 3–9) | 154 whole-ROM scans | 0 clean table (all hits in switch jump tables, e.g. 0x08082854, or compressed data) |
| Thumb `cmp rN,#button-mask` byte signature | 1,676 instructions, 40 clustered candidates triaged | 0 sequence validators |
| `strcmp`/pointer chain to a code-entry buffer | all literal pointers to the 0x08048xxx text bank (5 pointers) | all are cheat-name/UI accessors |
| Code-like `[A-Z0-9]{4,16}` strings | 5,695 candidates (2,600 containing digits) | 0 validators — trick names, credits, compressed-data noise |
| Reachable screens walked | 11 (splash ×2, story intro, ENTER NAME, CHANGE OUTFIT, tutorial gameplay, PAUSED, PAUSED→OPTIONS, SKATE SHOP, main menu, main OPTIONS, CHEATS) | no code-entry field on any |

**Gate domain (bounded gated-feature proof).** `CheatUnlock` has exactly one BL caller
(`0x08000B36`, verified by full-ROM Thumb BL scan). Its index argument comes solely from the
18-entry map at 0x08048A08 and is rejected when equal to `0xFFFFFFFF`. Since 15 is absent from
the map's value set, bit 15 can never be set by a reachable path. A live A-press on a locked row is
the in-game rejection: `STUD MODE` stayed `OFF` and both masks read `0x00000000` before and after
(savestates `game.ss1`/`game.ss2`).

**Button-code rejection (observed).** The published Skip Tutorial code at the main menu
(`game.ss3` → `game.ss4`) left `unlock_mask = 0x00000000` and `active_mask = 0x00000000`; the only
visible result was the menu cursor moving to STORY, which is explained by the D-pad presses
themselves. No `New Cheat` toast, no spin/flash confirmation, no state change attributable to a
code. This bounds *this input path and timing* (60–70 ms holds) only.

**Font/tile text-bank check before the negative.** UI text in this build is plain NUL-terminated
ASCII (cheat names at 0x48C74, "Cheats" at 0x48D90, "New Cheat" at 0x489FC), so `strings` sees the
actual UI. The create-a-skater letter bank at 0x4DD00 is lower-case ASCII drawn as capitals; its
38 on-screen cells (36 letters/digits + backspace + accept) contain no code/checksum glyphs. No hidden `PASSWORD`, `ENTER CODE`, `INVALID`
or `CODE MACHINE` string exists in any ASCII, lower-case or ±0x20 form. The negative is therefore
about the whole accessible text bank, not a blind `strings` miss.

## 7. Validation evidence

* **Observed** — every screen in §3; 15 CHEATS rows and wrap-after-15; locked toggle staying OFF;
  savestate reads of `0x02000008 → 0x0200D364`, both masks 0; published button code producing no
  flag change; no effect from long vs short key holds where tested.
* **Derived** — all function addresses and bit operations from Thumb disassembly; cheat/pointer
  table layout; skater→cheat map and its `-1` sentinel; the `cmp r7,#14` menu bound; the KEYINPUT
  polarity; the global slot path; cross-references (1 caller of `CheatUnlock`, 2 of `CheatName`,
  21 of `CheatSetActive`).
* **Inferred** — which named pro skater occupies map slots 14/15/16 (based on the credits order
  Tony Hawk … Jamie Thomas, Paul Rodriguez, Arto Saari, Mike Vallely); that `nergets` was a
  developer-only art/debug mode; that the goal-check routine's completion test is the 100%
  Arcade condition described by the guides (the check function itself was not fully decompiled).

## 8. Unknowns

1. Whether the published Skip Tutorial button code works on this revision with a different
   trigger context (e.g. title screen rather than main menu), a different debounce window, or a
   validator implemented in the game's script VM rather than ARM code. No mask table or comparison
   chain was found; the claim is recorded as unverified, not disproved.
2. The gameplay effect of cheat 15 `nergets` (name suggests a developer art mode). Its bit can be
   addressed in RAM but no in-game path sets it.
3. The exact skater identities for map slots 14/15/16 — inferred from the credits list, not read
   from a save record with 100% completion.
4. Never obtained a 100%-complete Arcade save, so the `New Cheat` toast path was derived from code,
   not observed in the emulator.
5. The standalone SKU was analysed independently; the 2-in-1 pack and sibling Tony Hawk games were
   not used as evidence.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo`.
* Python 3 `struct` scanners: literal pointers, Thumb BL xrefs (`0x08004B94` etc.), KEYINPUT
  literals, 154 button-sequence encodings, 136 published-password encodings, `[A-Z0-9]` code-like
  strings, `cmp rN,#imm` signature scan.
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`; Capstone for
  the attempted instruction-level scan.
* mGBA 0.10.5: `-3`, savestates (`Shift+F1`…`F4`), GDB stub (flaky: closed after first client and
  produced packet errors on reconnect) and `-d` pty debugger (`continue` works, but no reliable
  break-in without a controlling terminal). Final RAM evidence used savestate decoding.
* Savestate decoder: `.ssN` PNG → zlib-decompress the `gbAs` chunk → 0x61000 raw bytes; EWRAM at
  raw 0x21000, IWRAM at 0x19000 (guide §16.13). Scripts in `/tmp/opencode/thug/`: `ss.py`,
  `diffss.py`, `scan1.py`, `scan2.py`, `xref.py`, `btnsearch.py`, `btnfull.py`, `negative.py`,
  `keyin.py`, `k.py`, `kcode.py`, `dbg.py`.
* Web recon (data only, never instructions): GameFAQs GBA/PC/PS2/GC cheat pages and FAQ 28373,
  cheatcodes.com "The Cheats And How To Unlock Them", Neoseeker GBA cheats, Planet Cheats,
  SuperCheats, Almars CodeBreaker address list.

No ROM or copyrighted assets are redistributed; only hashes, addresses, algorithms and findings
are published. All emulator artifacts were written to `/tmp/opencode/thug/`, not the ROM folder.
