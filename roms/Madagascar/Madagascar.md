# Madagascar (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Madagascar.gba` (8,388,608 bytes / 0x800000) |
| Header title | `MADAGASCAR` |
| Game code / maker | `BGZE` / `52` (Rev. 00) |
| Entry word | `0xEA00002E` — stock GBA ARM branch to `0x080000C0` |
| Fixed `0x96` / complement / checksum | `0x96` / `0xFE` / `0x0000` |
| MD5 | `97af9c00a5718832b7e5e46f9e434820` |
| SHA-1 | `3f1e8c5ecea68cf812acffa4670f0f30266c5952` |
| SHA-256 | `91ad85e8582f3a78f93f9d24567ca8e28e2b1bbfadf3246111e232b50e3f94e6` |

Phase 0 findings: exactly **one** Nintendo-logo hit (file `0x4`, header `0x0`) — not a multiboot/
2-in-1 image. No appended trainer, no cracktro patch (entry word is the stock branch), no
second header. The `.sav` produced is 512 bytes (EEPROM 4 Kbit). This is the original
`Madagascar` (Vicarious Visions / Activision, 2005), **not** `Madagascar: Operation Penguin`
(BGPE) — the distinction matters because the published button codes are shared between the
two SKUs. `roms/INDEX.md` was not modified (per task instruction).

## 2. Executive summary

**No developer-intended cheat/password system exists in this ROM.** There is no password
screen, no button-code table, no debug menu, and no cheat flag. The only entry surface that
resembles a code field is the 3-character **"Enter Initials"** keypad; it is a *save-slot
label* (the save record is displayed as `"%s - %d%%"` in the slot list), not a validator.

The two published button codes — GameFAQs "Christmas mode"
(`Up,Left,Left,Right,Right,Left,Down,Right`) and "Super Jump"
(`L,R,Up,Down,R,L,Left,Right`, hold Select) — were **tested in live gameplay in every
documented variant** (with and without Select held; shoulder `L/R` and d-pad `Left/Right`
readings; both shoulder-bit assignments; multiple key timings). Neither produced a visible
effect, a screen change, or a persistent RAM flag difference. An exhaustive literal search of
all 8 MiB for the two sequences under **96 encodings** (Select OR on/off, active-high/low,
forward/reverse, u16/u32, both L/R bit conventions) returned **0 hits**.

The game's genuine "unlockables" are progression gated in the EEPROM save: the **Bonus**
menu entry is greyed out with `Next Bonus at 80` coins, and ability/bonus-level collection is
driven by coin totals (the level-select/ability gallery lists 23 named entries; fan sources
quote `Alex's Claws` at 740 coins and `Alex's Claw Climb` at 1120 coins, matching the in-game
`Total 0/1120` counter). These are save-progress unlocks, not cheats, and are reported as
such (§16.18 of the guide).

All on-screen text was found as **plain ASCII** in a pointer+string bank at
`0x08BA59C–0x08BA928`; there is no tile-indexed hidden text bank to decode. The only glyph
indirection in the bank is the sleep prompt `Press\nSELECT + \x86 + \x87\nto wake`, where
`0x86/0x87` are L/R shoulder icons — decoded, and not a cheat.

## 3. How to reproduce

Environment: `Xvfb :315 -screen 0 1024x768x24`, `openbox`, `SDL_AUDIODRIVER=dummy`,
`mgba -3 <rom>` (mGBA SDL). Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`,
Select=`BackSpace`, D-pad=arrow keys. Keys held 80–250 ms; savestates via `Shift+F<n>`
save / `F<n>` load. All test artifacts live in `/tmp/opencode/madagascar/`.

Path traversed (all screens observed, not inferred):

1. Boot → Activision attract → title (**Start Game**, **View Credits**).
2. Start Game → **Select a Slot** (3× `New Game`, `Erase`).
3. New Game → **Enter Initials: ---** keypad (`A–Z - ! ? ⚡ & OK`, 31 symbols; 3-char limit).
4. OK → **Adventure / Total 0/1120 / Bonus / Next Bonus at 80** (Bonus greyed/locked).
5. Select Adventure → **level-select gallery**: `"Alex's Double Jump"` with a 23-item left
   rail; only the first item is selectable on a fresh save (Up/Down/Left/Right do not move the
   selection). Pressing the locked `Bonus` entry lands on the same gallery.
6. A → level 1 cutscene → gameplay (HUD `0/75` coins, 5-segment health).
7. In gameplay: Start → **pause menu** (`Resume`, `Quit Level`, `Sleep`, `Sound`).
8. Sound → **Music Volume : 80% / SFX Volume : 100%** (no hidden options).
9. Title → View Credits → scrolling **Vicarious Visions, Inc.** credits.
10. Hidden-menu probes on title/gameplay: `L+R+Start+Select`, `L+R+A+B`,
    `Start+Select+A+B`, `L+R+Up+A` — no debug screen appeared in any case.

Screenshots (kept on disk, not attached): `s_title3.png`, `s_slot.png`, `s_init.png`,
`s_adv_again.png`, `s_level3.png`, `s_play.png`, `s_pause2.png`, `s_sound.png`,
`s_credits2.png`, `dbg0..dbg3.png`, `s_xmas_live.png`, `s_super_live.png`.

Published codes tested in live gameplay (after confirming the core was actually running —
an early false negative was caused by an mGBA GDB-stub session leaving the core halted):
- `Up,Left,Left,Right,Right,Left,Down,Right` (GameFAQs wording), plain and with Select held.
- `Up,L,Left,R,Right,L,Down,R` (shoulder reading), with Select held.
- `L,R,Up,Down,R,L,Left,Right`, with Select held (GameFAQs/Neoseeker/Fandom).
- Same with 50 ms and 100 ms inter-key holds.

None changed the screen, the coin counter, the health bar, or the persistent RAM state.

## 4. Address map

| Item | Address / value | Evidence |
|---|---|---|
| ROM header / entry | `0x08000000` / `0xEA00002E` | Observed (xxd) |
| Nintendo logo (only one) | file `0x4` | Derived (logo scan) |
| Key reader: `return 0x3FF ^ (u16)KEYINPUT` | `0x08005204` (Thumb) | Derived (objdump) |
| Key-state tracker (mask/current/held/pressed at +0/+4/+8/+12) | `0x080051DC` | Derived (objdump) |
| Engine vtable slot holding `0x08005205` | file `0x7F76B8` | Derived (pointer scan) |
| UI string bank (`{u32 ptr; char[]}` records) | `0x080BA59C–0x080BA928` | Observed |
| Candidate u32 key-mask arrays (inspected, **not** codes) | `0x080321C8`, `0x08032D34` | Derived |
| Game screen-state byte (EWRAM) | `0x020000B4`: title `0x24`, Adventure `0x34`, gameplay `0x09`/`0x00` | Observed (savestate RAM) |
| Save format | EEPROM 512 B; 3 slot headers at `0x00/0x60/0xC0` with `C0 DE 60 xx` magic | Observed |

File-offset ↔ ROM-address: `rom_addr = 0x08000000 + file_offset`.

mGBA `.ss1` layout used for RAM proof (§16.13): PNG with zlib-compressed `gbAs` chunk →
`397312` raw bytes; EWRAM begins at raw `0x21000`, IWRAM at raw `0x19000`. Therefore raw
`0x210B4` = EWRAM `0x020000B4`. Title↔Adventure differ in only **4 bytes** in the first
16 KiB of EWRAM (`0x020000B4: 0x24→0x34`, and a pointer at `0x020000BC`), which identifies
`0x020000B4` as the screen-mode byte (Observed).

## 5. Algorithm

No validator exists, so there is no algorithm to reimplement. The negative result is based on
the following searches, all reproducible:

1. **Literal sequence search** — for each of the three published variants, encode the 8
   button masks as u16/u32 little-endian, with Select OR'd on/off, active-high vs
   `(0x3FF ^ x)`, forward and reversed, and both shoulder assignments
   (`R=0x100,L=0x200` and `R=0x200,L=0x100`): **96 encodings tested, 0 hits** anywhere in
   the 8 MiB (`button_search_evidence.txt`).
2. **Mask-run census** — scan every 2-byte offset for runs of ≥8 values drawn from the
   10 valid single-button masks: **28 candidate runs**, all in data blocks
   (`0x0321C4`, `0x032D2C`, `0x0B4870`, …); none matches either published sequence. The
   two u32 arrays at `0x080321C8`/`0x08032D34` are the closest candidates but decode to
   `8,8,10,10,20,20,40,40,10,8,20,8,20,10,40,20,…` — not a published code.
3. **Text search** — `strings -t x -n 4` yields 84,890 strings. Case-insensitive census:
   `password` **0**, `cheat` **0**, `debug menu` **0**, `level debug` **0**, `konami` **0**,
   `code` **8** (all libjpeg/GAX engine diagnostics: "Invalid SOS parameters", "Bogus message
   code %d", `Code: B.Wodok`), `secret` **1** and `unlock` **2** (both in story dialogue).
   UTF-16LE/BE/UTF-32 searches for `Christmas`, `Super Jump`, `cheat`, `debug`,
   `level select` returned **0 hits**. No font/tile-indexed hidden text bank exists: every
   visible label (`Start Game`, `View Credits`, `Select a Slot`, `Enter Initials`,
   `Adventure`, `Bonus`, `Next Bonus at %d`, `Resume`, `Quit Level`, `Sleep`, `Sound`,
   `Music Volume :`, `Alex's Double Jump`, `Vicarious Visions`) is present verbatim as ASCII
   in the bank above.
4. **Input-surface test** — live gameplay entry of all documented variants (§3) with RAM
   diff before/after (`xmas_before2.ss` vs `xmas_after2.ss`): 2,304 differing bytes, all
   attributable to animation/timers/RNG and the moving character; **no new persistent flag**
   and no palette/VRAM theme change (the palette-region differences are the existing white
   cloud animation).
5. **Debug-gate probe** — four standard hidden-menu combinations on the title screen (§3),
   no hidden screen.

The `0x04000130` key-reader convention (active-high mask `A=1,B=2,Select=4,Start=8,
Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200`) is Derived from the function at
`0x08005204`, so the masks used in searches 1–2 are the engine's own, not assumed.

## 6. Tables

**UI string bank** (`0x080BA59C–0x080BA928`), `{u32 ptr; NUL-terminated ASCII}` records —
relevant rows:

| File offset of pointer | Points to | String |
|---|---|---|
| `0xBA5DC` | `0x080BA5D0` | `Start Game` |
| `0xBA5F0` | `0x080BA5E0` | `View Credits` |
| `0xBA650` | `0x080BA640` | `Select a Slot` |
| `0xBA664` | `0x080BA654` | `Erase a Slot` |
| `0xBA68C` | `0x080BA67C` | `Music Volume : ` |
| `0xBA6A0` | `0x080BA690` | `SFX Volume : ` |
| `0xBA76C`–`0xBA7B0` | `0x080BA764`… | `Resume`, `Quit Level`, `Quit Game`, `Quit`, `Sleep`, `Sound` |
| `0xBA848` | `0x080BA828` | `Press\nSELECT + \x86 + \x87\nto wake` (glyph indices = icons) |
| `0xBA860` | `0x080BA84C` | `Enter Initials: ---` |
| `0xBA874`/`0xBA88C`/`0xBA89C` | … | `Defeat Section`, `Defeat Section 100%`, `Slow Motion` (results/ability labels) |
| `0xBA8B4`/`0xBA8C0`/`0xBA8E8`/`0xBA900` | … | `Adventure`, `Bonus`, `Total %d/%d`, `Next Bonus at %d` |

**Initials keypad alphabet (31 selectable cells + OK)**: `A B C D E F G H / I J K L M N O P /
Q R S T U V W X / Y Z - ! ? ⚡ & OK`. This is a name-entry alphabet (3 characters max), not
a password alphabet; the recorded initials are consumed as the `%s` of `"%s - %d%%"` in the
slot list.

**Unlock gating (Observed/Derived)**: `Total n/1120` coin counter; `Bonus` entry disabled
until 80 coins (`Next Bonus at 80`); 23 named gallery entries from `Alex's Double Jump`
(`0x080BA92C`) through `Wild World`, `Penguin Fishing`, `Foosa Arena`, etc. No button code
feeds these flags — they are EEPROM progression data.

## 6b. Enumeration

Per §0.2, the "space" and its bounds are stated even though the result is negative.

- **Button-code space searched**: 3 published sequences × 2 L/R conventions × 2 Select
  states × 2 polarities × 2 directions × 2 integer widths = **96 encodings**, 0 ROM hits.
- **Generic key-sequence tables**: **28** u16 runs of length ≥8 over the 10 valid key
  masks; 0 match a published code. Also scanned for u32 runs containing Select: 302 runs,
  all in compressed graphics/audio data, none code-like.
- **Text space**: 84,890 ASCII strings + 3 alternate Unicode encodings × 8 keywords;
  0 cheat/password/debug-menu labels.
- **Screen space**: 9 reachable screens + 4 hidden-menu combinations probed; every screen
  listed in §3 was entered and screenshotted with a contemporaneous savestate.
- **Live entry**: both published codes, each in every published wording, with three key
  timings; 0 accepted, 0 state changes beyond ordinary gameplay animation (RAM diff).
- **Bounds proven by rejection**: the game rejects the published codes (no flag set, no
  palette/theme change, no warp, no HUD change). The `Bonus` menu entry rejects selection at
  0 coins with the explicit on-screen bound `Next Bonus at 80` (Observed); the level gallery
  likewise permits only its first entry on a fresh save. These are the in-game rejection
  results that bound the "cheat" and "unlock" spaces respectively.
- **No novel code minted**: with no validator, no table, no alphabet and no code space, there
  is nothing to enumerate or generate. A fabricated "code" cannot be accepted by a system
  that does not exist; reporting one would be dishonest. This is a *bounded* negative over
  the spaces enumerated above, not an untested guess.

## 7. Validation evidence

- **Observed** — emulator screenshots and savestates for every screen in §3; EEPROM dump
  (`Madagascar.sav`); 96-encoding search output (`button_search_evidence.txt`); 0 literal
  hits for `Christmas`/`Super Jump`/`password`/`cheat` in any encoding.
- **Derived** — objdump of `0x08005204`/`0x080051DC` establishing the key-mask convention;
  pointer-table decode of the UI string bank; u32 mask-array census; savestate-diff
  identification of `0x020000B4` as the screen-mode byte.
- **Inferred (labelled)** — the mapping "initials = save label, not password" is inferred
  from the 3-character limit, the `"%s - %d%%"` consumer string, and the absence of any
  comparison against the entry buffer; it is not proven by an xref to a `strcmp` call.
  The coin-threshold values quoted from fan sources (740/1120 for two abilities) are
  **Inferred** from external documentation; the in-game `Total 0/1120` and `Next Bonus at
  80` are **Observed**.

One harness pitfall is worth recording: an mGBA `-g` session whose `continue` timed out left
the core halted, making all subsequent key input appear ignored. The first two "no effect"
code tests were discarded and repeated on a fresh non-`-g` instance; only those repeated
tests are reported above (§16.2 of the guide).

## 8. Unknowns

- Whether the two published codes are genuine `Madagascar: Operation Penguin` cheats that
  were mis-attributed to this SKU — plausible, given the identical code text on the two
  GameFAQs pages and the explicit "Press Select" wording on the Operation Penguin pages,
  but not verifiable from this ROM alone.
- Whether reaching 80+ coins and entering the unlocked `Bonus` screen reveals further
  screens (the screen is progress-gated; no save editor or memory patch was used, as that
  is outside the in-game-cheat scope).
- Exact EEPROM bit→ability mapping (the save uses checksummed 0xC0-byte records with
  per-slot headers; only the coin counter and the `Bonus` gate were exercised).

## 9. Tooling

`strings`, `xxd`, `grep`, Python 3 (capstone 5.0.7 for Thumb disassembly/pointer and literal
scans), `arm-none-eabi-objdump -M force-thumb`, mGBA SDL under Xvfb :315, `xdotool`, `scrot`,
`zlib` + a custom savestate parser (`ssdiff.py`) for `gbAs` RAM diffs. Web sources consulted:
GameFAQs (Madagascar GBA cheats, 2-in-1 pack, Operation Penguin), SuperCheats, Neoseeker,
Fandom cheat wiki, VGChartz, TCRF (no Madagascar GBA page exists). All fetched pages were
treated as data; no prompt-injection payload was encountered in this run. No ROM or
copyrighted asset is redistributed here — only addresses, hashes, and findings.

## 10. Cleanup

All emulators and display servers started for this job were stopped by their own PIDs
(Xvfb/openbox :315 and the mGBA instances), and all generated `.sav`/`.ss*` files were
removed from `/mnt/gbacheats/roms/Madagascar/`. `roms/INDEX.md` was left unchanged as
instructed.
