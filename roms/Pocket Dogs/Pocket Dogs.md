# Pocket Dogs (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Pocket Dogs.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `POCKETDOGS` |
| Game code | `BTDE` |
| Maker | `GG` |
| Version | 0x00 (Rev.00) |
| Entry branch | `0xEA00002E` (stock branch to 0x080000C0) |
| Header complement byte | 0xB1 (header sum 0xE7 — rebuilt-header artifact, no cracktro) |
| MD5 | `480117b99ff0ce0934d5f4e3b5a952b4` |
| SHA-1 | `79a90b119ea84c5812575d20ba6107be7edbfee7` |
| SHA-256 | `e69c1fa888129f01a5884b19e0f74d8aa76097b82628ae95062a991fbd741dc3` |

Phase 0 scan: exactly **one** Nintendo-logo/GBA-header occurrence, at file offset 0. No
appended trainer, multi-game shell, or patched entry point. The first 4 KiB is a normal
ARM crt0. No patch/trainer present.

## 2. Executive summary

Pocket Dogs has **no password / cheat-code / button-code entry system**. The only
developer-intended hidden feature is a full **DEBUG MENU** with 12 selectable entries,
plus three additional standalone developer screens. All of them are driven by a single
byte in IWRAM: the scene ID at `0x03001258`.

Published 3rd party cheat indexes "codes" (`0300125802/03/04/0F`) are raw RAM writes that set this byte;
all four were verified against the ROM and reproduced in the emulator (§6). They are
**memory-edit codes and are not in-scope deliverables** — but the underlying developer
screens are real, shipped content and are enumerated in full below.

One genuine **in-game input trigger** exists: holding **B + Start at boot** sets the
scene ID to 0x0F and opens the *Delete saved data?* screen. This was proven with a live
breakpoint at the gate (§3, §7). No other button sequence, password alphabet, or hidden
keyboard was found: keyword scans across ASCII, case-shifted, UTF-16, and font-indexed
encodings returned only the ASCII `DEBUG MENU` literal, and no 3-press button-mask table
exists in the image.

The on-screen `Enter your name?` keyboard (reached via Mode Select → Talk and via the
debug menu's `Data Input`) is a **player-name field, not a password**: its alphabet is a
full name keyboard, it is the first-run naming step of normal play, and no comparison
against a constant exists nearby. Reported as a false positive, with the bounds of the
search stated (§8).

## 3. How to reproduce

Emulator: mGBA (SDL) under Xvfb `:318`, `SDL_AUDIODRIVER=dummy`, scale `-3`.
Keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
Hold 80–150 ms per press.

**Normal path to the hidden screens (debug menu):**
There is no in-game path to the debug-menu root. The developer screens are reached by
setting the scene ID byte. Two reproducible ways:

1. **Savestate patch (used for all screenshots):** save a state on the title screen
   (Shift+F1), decompress the PNG `gbAs` chunk, change byte at raw-state offset
   `0x1A258` (= IWRAM `0x03001258`; IWRAM begins at raw offset `0x19000`) to the desired
   scene ID, recompress, and boot with `mgba -3 -t patched.ss1 Pocket\ Dogs.gba`.
   The main loop sees requested(ID) ≠ current(`0x03004918`) and calls the scene init.
2. **mGBA CLI debugger (`mgba -3 -d`):** at the paused prompt use
   `w/1 0x03001258 2` then `c`. (Writing before the boot code runs is overwritten;
   patch after boot or break at `0x08000A3A` and inject there.)

**Walking the debug menu:** boot into scene 2. Navigate with Up/Down, select with A,
back with B. Each root entry was entered from a fresh copy of a saved scene-2 state
(loaded with plain `F1`) so the cursor started at index 0; the 12 entries were reached by
0–11 Down presses.

**In-game B+Start gate (no save patch needed):**
Launch a fresh emulator and hold B(`z`)+Start(`Return`) through the boot logo. Equivalent
breakpoint proof: `mgba -3 -d`, set `break 0x08000A3A`, `c`; at the break,
`r/2 0x03000C90` (held-key mask, active-high), `w/2 0x03000C90 10`, `c`. The
*Delete saved data? YES NO* screen appears with `0x03001258 == 0x0F`.

Published codes tested (all are raw RAM writes, verified semantically):
`0300125802`, `0300125803`, `0300125804`, `030012580F` — all accepted, all produced the
documented screen. `0300125813` (unpublished) was minted and accepted too (§6b).

## 4. Address map

| Item | Address | Notes |
|---|---|---|
| Scene ID (requested) | `0x03001258` | **byte**; main loop compares to current |
| Current scene | `0x03004918` | byte |
| Held keys (active-high) | `0x03000C90` | u16; `~KEYINPUT & 0x3FF`; gate reads this |
| Previous-held keys | `0x03000C94` | u16 |
| Pressed-this-frame keys | `0x03000C9C` | u16 |
| Scene-id setter | `0x08001098` | `strb r0,[0x03001258]`; 61 in-game callers |
| Input handler | `0x08001894` | reads `0x04000130`, builds masks above |
| A+B+Select+Start reset | `0x080010B0` | calls soft-reset `0x08031320` |
| Boot gate check | `0x08000A3A` | `if ((held & 0x0A)==0x0A) scene=0x0F` |
| **Scene-init pointer table** | `0x081B7668` | u32[≥36] indexed by scene ID |
| Scene 2 init (debug menu) | `0x08025890` | → text `0x08158360` |
| Scene 3 init (CHR test) | `0x08025451` | |
| Scene 4 init (position test) | `0x08025615` | |
| Scene 0x0F init (delete data) | `0x080092E1` | |
| Debug-menu entry table | `0x081BE034` | 12 records × 24 bytes |
| Debug-menu root cursor | `0x02004710` | u16 |
| MESS TEST cursor | `0x02004712` | u16, wraps 0..3 |
| MESS TEST state word | `0x0300490C` | u16 (1 = active) |
| Debug text literals | `0x08158360`..`0x08158448` | "DEBUG MENU", sub-screen labels |
| Font/index table | `0x081BE1B4` | 256-byte char→tile map (checked for encoded text) |

## 5. Algorithm

The "cheat system" is a **scene selector**, not a validator:

```
boot:
  scene_requested = 6                       # 0x08000A30..A34
  read_input()                              # 0x08001894, fills 0x03000C90
  if (held_keys & 0x0A) == 0x0A:            # B + Start (active-high bits 1|3)
      scene_requested = 0x0F                # Delete Data screen

every frame (main loop ~0x0800A5C):
  if scene_current != scene_requested:
      scene_current = scene_requested
      call scene_init_table[scene_requested]   # 0x081B7668

debug menu (scene 2), root handler ~0x08025A00:
  cursor = *(u16*)0x02004710                 # Up/Down skips records with flag==0
  A -> dispatch record[cursor] by its flag/action field:
         flag 0x14 -> MESS TEST parameter screen (stays scene 2)
         flag 0x06 -> scene 6   (boot/title intro)
         flag 0x0A -> scene 0x0A (name entry)
         flag 0x05 -> scene 5   (main / demo mode)
         flag 0x01 -> PUZZLE parameter screen (stays scene 2)
         flag 0x08 -> scene 8   (Book Puzzle! minigame)
         flag 0x09 -> scene 9   (Find Pocket Dogs! minigame)
         flag 0x07 -> scene 7   (DOG VIEWER)
         flag 0x10 -> scene 0x10 (OMAKE Viewer)
         flag 0x12 -> scene 0x12 (15PAZ Viewer)
         flag 0x05 -> scene 2   (SOUND TEST sub-screen)
```

There is no checksum, no alphabet, no string comparison, and no length check. The
"code space" is the 8-bit scene ID, of which four values (2, 3, 4, 0x0F) are the
developer screens documented by 3rd party cheat indexes and the rest are ordinary game scenes.

## 6. Tables

**Published RAM-write codes — verification results:**

| 3rd party cheat index code | Value written | Screen observed | `0x03001258` read back | Result |
|---|---|---|---|---|
| `0300125802` | 0x02 | DEBUG MENU (12 entries) | 0x02 | ✓ |
| `0300125803` | 0x03 | CHR TEST (tile mosaic, "Stage PAUSE") | 0x03 | ✓ |
| `0300125804` | 0x04 | POSITION test (XPOS/YPOS/ROT) | 0x04 | ✓ |
| `030012580F` | 0x0F | "Delete saved data? YES NO" | 0x0F | ✓ |

All four strings/literals were also checked against the ROM: the debug-menu text is at
`0x08158360` exactly as 3rd party cheat indexes state. No 3rd party cheat index code exists
for this title (all three report zero cheats; verified via archived pages). These are
**memory-edit codes, not in-scope cheats** — recorded only as verification of the
developer screens.

**Debug menu — all 12 entries (ROM table 0x081BE034, 24-byte records; screenshot + RAM mode):**

| # | Label | Target scene ID | Observed screen | RAM proof |
|---|---|---|---|---|
| 0 | Mess Tesr | 2 (in-menu) | `<Message Test>`: DogTy, M Type, M No, Randam | mode 0x02; cursor `0x02004712` |
| 1 | Title Menu | 6 | "Licensed by Nintendo" boot screen | mode 0x06 |
| 2 | Data Input | 0x0A | "Enter your name?" keyboard | mode 0x0A |
| 3 | Main Mode | 5 | Tutorial / gameplay with player dog | mode 0x05 |
| 4 | Main Mode(DEMO) | 5 | Demo dog animation, gray background | mode 0x05 |
| 5 | Minigame "PUZZLE" | 2 (in-menu) | `<Minigame "PUZZLE">`: STAGE 1, Nolma 50, Ojama 0, Time 100, Range 4 | mode 0x02 |
| 6 | Minigame "15 PANEL" | 8 | "Book Puzzle!" menu (Start Game / How to Play / Exit) | mode 0x08 |
| 7 | Minigame "TAKARA" | 9 | "Find Pocket Dogs!" menu (Start Game / How to Play / Exit) | mode 0x09 |
| 8 | Dog Viewer | 7 | `DOG VIEWER`: TYPE / POSE / ACT / SIZE 100% | mode 0x07 |
| 9 | OMAKE Viewer | 0x10 | Bonus dog CHR image (chihuahua in pink outfit) | mode 0x10 |
| 10 | 15PAZ Viewer | 0x12 | Bonus CHR image, tiled/mirrored display | mode 0x12 |
| 11 | Sound Test | 2 (in-menu) | `<Sound Test>`: BGM, SE, DOG, ZING, S No | mode 0x02 |

Every entry has an effect — there are no dead/unlabelled entries. The three entries that
keep mode 2 are drawn as sub-screens by the debug-menu handler itself; their selection
state is in `0x02004710`/`0x02004712`/`0x0300490C`.

**Standalone developer screens (outside the 12-entry menu):**

| Scene ID | Init function | Screen |
|---|---|---|
| 0x03 | 0x08025451 | CHR TEST (scrolling tiles, numerals, SCORE/GOAL/TIME/START/JUMP) |
| 0x04 | 0x08025615 | POSITION TEST (`XPOS: / YPOS: / ROT:`) |
| 0x0F | 0x080092E1 | Delete saved data confirmation |

**Gate bits:** `0x03000C90 & 0x0A` — bit 1 = B, bit 3 = Start (active-high masks).
`0x03000C90 & 0x0F == 0x0F` (A+B+Select+Start) calls `0x080010B0` (soft reset), not a cheat.

## 6b. Enumeration

**Space definition:** the selector is a single unsigned byte at `0x03001258`, so the
representable space is 256 values (0x00–0xFF). 36 entries of the init table at
`0x081B7668` were dumped; every probed value dispatches to a real scene. The developer
subset documented by 3rd party cheat indexes are `{0x02, 0x03, 0x04, 0x0F}` (4 values). No checksum, field
width, reserved bits, or alphabet exists to enumerate further; completeness for the
*debug-menu* surface is established by (a) the 12-record table at `0x081BE034` being
fully walked, and (b) the init table being indexed directly by the byte with no hidden
qualifier.

**Novel value (not on 3rd party cheat indexes / any wiki): `0x13`.**
Minted by patching `0x03001258` to `0x13` in a title-screen savestate and booting with
`-t`. Result: `0x03001258 == 0x13` and the game displays the distinct cutscene
"Is that your Pocket Dog I hear!" with a door graphic — a screen no published code lists.
(Scene 0x13 maps to init `0x080086C9` in the table.)

**Bounds proven by rejection / exhaustive checks:**

- The on-screen keyboard accepts a *name*, not a code. Typing ordinary name characters
  merely fills the name field; no accept/reject path or validator call was found (§8).
- The 12-entry table's `flag` field at record offset +20 is the dispatch key. Entries
  whose flag is 0 would be skipped by the Up/Down loop at `0x08025A66`; all 12 records
  have nonzero flags, so the menu is complete — there is no 13th hidden entry. The byte
  after the 12th record is zero, terminating enumeration.
- 3-press button-mask table search: **0 hits** for u16 little-endian sequences of the
  standard active-high masks (e.g. Up,Up,Down / B,Start prefixes) — no Konami-style
  button code can exist in that encoding. The apparent `BStart` u16 hits (22) are
  incidental data in graphic/audio tables, verified by dumping the context.
- Keyword scan: `PASSWORD`, `CHEAT`, `SECRET`, `UNLOCK`, `CODE` → **0 hits** in ASCII,
  upper-case, +0x20 case-shifted, UTF-16LE/BE, and font-index encodings. Only `DEBUG`
  hits, at `0x08158360`. Conclusion of "no password system" is bounded by these spaces.

## 7. Validation evidence

Labels: **Observed** = emulator screenshot / savestate RAM read / live debugger;
**Derived** = instruction sequence; **Inferred** = plausible but not fully exercised.

- **Observed** — single 8 MiB header, stock entry, hashes (§1).
- **Observed** — DEBUG MENU root and all 12 sub-screens; screenshots `05_debugmenu.png`,
  `06_after_A.png`, `e0..e11.png` in `/tmp/pocketdogs/`.
- **Observed** — `0x03001258` read back as 0x02/0x03/0x04/0x0F/0x13 for each patched boot,
  and 0x05/0x06/0x07/0x08/0x09/0x0A/0x10/0x12 for the corresponding scene entries,
  always matching `0x03004918` (current scene).
- **Observed** — live breakpoint at `0x08000A3A` halted with `r0=0x08000A3B`,
  `r5=0x03001258`, disassembly `ldr r0, =0x03000C90`. Injecting 0x000A into
  `0x03000C90` then continuing produced the Delete Data screen with mode 0x0F.
- **Derived** — boot gate `if ((held & 0x0A)==0x0A) scene=0x0F` from
  `0x08000A3A..A4A`; input mask construction at `0x08001894..8F4` (`mvns` on KEYINPUT).
- **Derived** — scene table `/081B7668`, 12-record menu table `0x081BE034`, root cursor
  `0x02004710`, MESS TEST cursor `0x02004712`, via literal-pool xrefs from the handlers.
- **Observed** — normal flow: title `PRESS START` (mode 5) → Start → Mode Select
  (mode 6) with highlighted `Talk` → A → `Enter your name?` (mode 0x0A). Note: Start on
  the title loops back to the boot logo when the SRAM contains a stale save; with a
  clean/no `.sav` it advances to Mode Select. Environment quirk, not a game cheat.
- **Inferred** — the `abc` button on the name keyboard switches character sets; not
  exercised because it is irrelevant to the cheat question.
- **Inferred** — the published raw-RAM codes are the only "codes" that ever existed for
  this SKU; no password-generation routine was found, but an unreferenced generator
  could in principle be buried in compressed data not scanned here.

## 8. Unknowns

- Whether any of the remaining scene IDs (0x00, 0x01, 0x0B–0x0E, 0x10–0x12, 0x14+) are
  reachable by ordinary play; only 0x13 was minted as an unpublished example. Their
  init functions exist in the table; they were not individually screenshotted.
- The exact purpose of the `abc` toggle and the secondary character rows on the name
  keyboard; not tested (no relation to cheat content).
- Pause/Options screens of the full gameplay loop were not exhaustively walked: the
  game's Mode Select list only exposed `Talk` in a fresh save, and Down/Right did not
  move the highlight, so other modes are likely gated by save progress. No hidden code
  surface was observed there.
- A theoretically possible password generator hidden in compressed graphics/audio was
  not decompressed; the literal/keyword/button-mask searches all returned negative.

## 9. Tooling

- `strings -t x`, `xxd`, `grep -abo` for reconnaissance.
- Python + Capstone 5.0.7 / `arm-none-eabi-objdump -M force-thumb` for literal-pool xrefs,
  scene-table decoding, and keyboard scans.
- mGBA SDL under Xvfb `:318` + openbox; `xdotool` XTEST input; `scrot`/ImageMagick crops.
- Savestate RAM reads: PNG `gbAs` chunk → `zlib.decompress` → IWRAM at raw offset
  `0x19000`; scene byte at `0x1A258`. Scripts: `ssread.py`, `sspatch.py`, `snap.sh`,
  `enter.sh`, `go.sh` in `/tmp/pocketdogs/`.
- mGBA CLI debugger (`-d`) driven through a PTY for the live breakpoint proof
  (`dbg2.py`/`dbg3.py`, `dbgcmd.sh`); GDB stub on :2345 was unavailable (held by another
  process), so the PTY debugger and savestate diffing were used instead (guide §16.13).
- Web: 3rd party cheat indexes via `web.archive.org` snapshot (403 direct); 3rd party cheat indexes
  checked and contain no codes for this SKU. Fetched page content was treated as data;
  no prompt-injection payload was encountered in this session.

## 10. Legal note

No ROM image, extracted graphics, or game text assets are redistributed. Only addresses,
hashes, algorithms, and original analysis scripts are published.
