# Fantastic Four: Flame On (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Fantastic Four: Flame On.gba` |
| Size | 8,388,608 bytes (8 MiB) |
| Header title | `F4 FLAME ON` |
| Game code | `BH4E` (region E = USA) |
| Maker | `52` (Activision) |
| Version | `0x00`; complement `0x2B`; header checksum `0x0000` |
| Header check | `sum(ROM[0xA0:0xBE]) + 0x19 = 0x00` → valid, not a rebuilt header |
| MD5 | `098752d6f195ab8c34e0eebad3a0a779` |
| SHA-1 | `c2f979e257608dc3425e9567a14a8a514443e614` |
| SHA-256 | `76617921c67e554e17ccba15255e3e30ce67dee1043f74b3d15639d07a43e738` |

`file(1)` reports `Game Boy Advance ROM image: "F4 FLAME ON" (BH4E52, Rev.00)`.
Embedded-header scan: **one** Nintendo-logo hit (file `0x4`, header `0x0`) — a single
retail image, no multiboot stub, no appended trainer, no cracktro (entry word
`0xEA000030` → stock crt0 at `0x080000C0`). Engine strings identify Torus Games,
built `Aug 26 2005` / `Aug 27 2005 12:50:58` (file `0x8960C`, `0x8AD50`).

Sibling check: `roms/Fantastic 4/Fantastic 4.gba` is a **different** 16 MiB image
(title `FANTASTIC4`, code `BF4E`, MD5 `04105c845973df1d717b2487227f0fb0`). It shares
the Torus engine and two of the three button sequences (see §6b), but its published
code `B,A,Left,Select,A` is **absent** from this ROM and this ROM's `BADASS` code is
absent from the sibling. No asset, table or address from the sibling was used here.

## 2. Executive summary

This game has an **in-game button-code system** on the title screen, not a password
system and not a cheat-device system. Three button sequences are registered by the
title-screen state. The published "BADASS" sequence
`B, A, Down, A, Select, Select` opens a hidden **EXTRAS / cheat menu** containing
`GIMME HEALTH` and `GIMME POWER` checkbox items. Two further, **unpublished**
sequences (`Up,Down,Up,Right` and `Left,Right,Left`) are accepted by the very same
validator but do not open the menu and do not unlock the BONUS items; their effect
is still unknown (see §8).

The codes are stored as little-endian `u16` active-high key masks, terminated by
`0xFFFF`, and are validated by a generic 24-byte-record sequence detector in the
Torus engine. There is no alphabet, checksum or generator: the **complete code
space is exactly the three registered sequences** (3 codes; lengths 3, 4 and 6).
A novel near-miss sequence was pressed in the emulator and rejected (breakpoint at
the completion handler did not fire), bounding the space by rejection.

All CodeBreaker/GameShark/Action Replay listings found on the web are memory
patches and are out of scope; none were applied. The console-version codes
(PS2/Xbox/GC "Hell" unlock, Stan Lee interview, infinite cosmic power) are for
other SKUs and do not apply to this GBA image.

## 3. How to reproduce

Emulator: `mgba -3` under `Xvfb :315`, `SDL_AUDIODRIVER=dummy`, keymap
A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows.
Hold each key ~70–100 ms with a ~70 ms gap; release fully between presses.

1. Boot. The game shows a legal splash, then an attract **DEMO** with a `DEMO`
   banner.
2. Press **Start** on the DEMO; the Torus logo and `FANTASTIC 4` title animate in,
   then `PRESS START` blinks. The title screen is transient (~1–2 s) before it
   falls back to DEMO, so enter the code as soon as the purple title is up.
3. On the title screen press `B, A, Down, A, Select, Select` (mnemonic `BADASS`).
4. After a short transition the `EXTRAS` cheat menu appears with two items,
   `GIMME HEALTH` and `GIMME POWER`, each with a yellow ✗ box. D-pad Up/Down moves
   the orange highlight.

Verification with the debugger (stronger than the screenshot): launch
`mgba -d -3`, set `b 0x08073EE0`, `c`, enter a code. A hit at `0x08073EE0` with
`r1 = 0/1/2` and `r2 = 4/3/6` proves that particular sequence completed. A novel
sequence produces **no** hit.

## 4. Address map

All ROM addresses are `0x08000000 + file offset`.

| Item | ROM / file address | Notes |
|---|---|---|
| Button-code table | `0x0808ACC8`–`0x0808ACED` (`0x8ACC8`) | three `0x0000`-prefixed, `0xFFFF`-terminated `u16` mask arrays |
| Code pointer list | `0x080188DC`–`0x080188E4` (`0x188DC`) | `0x0808ACC8`, `0x0808ACD4`, `0x0808ACDE` |
| `AddSequence` | `0x08073D8C` (`0x73D8C`) | registers one 24-byte record; called exactly 3 times from `0x0801886C/78/84` |
| Step matcher | `0x080740E0` (`0x740E0`) | advances progress, returns 1 when `progress == length` |
| Completion handler | `0x08073EE0` (`0x73EE0`) | called with `(manager, code index)` on completion |
| Sequence manager | EWRAM `0x0200D074` | observed in `r0`/`r6` at the completion breakpoint |
| Cheat-menu text | `0x0807DC04F`, `0x0807DC05C`, `0x0807DC068`, `0x0807DC06E` | `GIMME HEALTH`, `GIMME POWER`, `OFF`, `ON` (ASCII bank) |
| Menu/level text bank | `0x0807DBF81`–`0x0807DC109` | `BONUS`, `HIGH SCORES`, `CREDITS`, `SNOWBOARDING`, `MOTO X`, five level names, `EXTRAS`, `PAUSED/RESUME/QUIT` |
| RTTI class names | `0x0808B218`/`0x0808B240` | `MainMenuState`, `CheatMenuState`; debug-only `Player Debug Screen` at `0x080895F4`, profiling menu at `0x080895F4`–`0x080897D0` |

Note: the visible UI strings **are** plain ASCII in this image (`strings -t x`
finds them); no font/tile-index decoding was needed for the negative findings.

## 5. Algorithm

Key masks are active-high `~KEYINPUT & 0x3FF`:
`A=0x001 B=0x002 Select=0x004 Start=0x008 Right=0x010 Left=0x020 Up=0x040
Down=0x080 R=0x100 L=0x200`.

`AddSequence(manager, table, timeout=0)` builds a 24-byte record:

```
record.lead        = u16 table[0]        # always 0x0000 (matches any frame)
record.seq         = &table[1]           # pointer to first real mask
record.length      = count of masks until 0xFFFF
record.progress    = 0
record.timeout     = timeout (0 = no timeout here)
record.timer       = 0
```

Per-frame update (`0x08073DE0`), for each record:

1. `held = ldrh [keyObject+0x28]`; if `held == 0`, skip all records.
2. If `held & record.lead == 0`, skip this record (lead is 0, so always passes).
3. `expected = record.seq[record.progress]`.
4. If `held == expected` (or the `0x1000`/`0x2000` special mask cases), call
   `StepMatch`: store `held`, `progress++`, reset timer; return
   `progress == length`.
5. Otherwise reset `progress = 0` — a wrong or simultaneous press restarts the
   sequence.
6. On completion, reset progress and call `Completion(manager, code_index)`.
7. A timeout count at `record+16` (here always 0) would reset an unfinished
   sequence after N frames.

This is an exact-match, edge-per-frame matcher: extra or held-over buttons cause a
reset; no checksum and no wildcard symbol exist.

## 6. Tables

| Index | Sequence | Masks (`u16`) | Length | Publicly documented? | Time to press |
|---:|---|---|---:|---|---|
| 0 | Up, Down, Up, Right | `40 00 80 00 40 00 10 00` | 4 | **No** | yes, completion observed |
| 1 | Left, Right, Left | `20 00 10 00 20 00` | 3 | **No** | yes, completion observed |
| 2 | B, A, Down, A, Select, Select ("BADASS") | `02 00 01 00 80 00 01 00 04 00 04 00` | 6 | Yes (classicgamehacking.com, GBA-US) | yes → cheat menu |

Published web codes:

| Source | Code | Verdict |
|---|---|---|
| classicgamehacking.com, "Cheat Menu – Fantastic 4: Flame on (U) (GBA)" | `B,A,Down,A,Select,Select` = BADASS | **verified** literally at `0x0808ACE0` and in emulator |
| GameFAQs `Fantastic 4` (sibling game) | `B,A,Left,Select,A` | belongs to the other SKU; **not present** in this ROM |
| GameFAQs console entries (PS2/Xbox/GC) | Hell unlock, Barge arena, infinite cosmic power | other platforms; not applicable |
| CodeBreaker/GameShark/Action Replay lists | memory patches | out of scope, not applied |

TCRF's fetched page contained an injected "decode key" instruction (write an
EICAR test string to `key.bin`). It was treated as untrusted data and ignored;
no action was taken on it.

## 6b. Enumeration

**Space definition.** The system is a fixed lookup of exactly **3** sequences,
not a checksum space. Total accepted inputs: **3** (lengths 3, 4, 6). Evidence that
the enumeration is closed:

* only three `BL` call sites reach `AddSequence` (`0x0801886C`, `0x08018878`,
  `0x08018884`), each with one of the three table pointers;
* the pointer list at `0x080188DC` has exactly three entries before unrelated data
  begins at `0x080188E8`;
* each sequence array ends at its first `0xFFFF` terminator;
* a scan for further `0x0000`-prefixed / `0xFFFF`-terminated mask arrays found no
  other registered sequence.

**Novel / unpublished codes.** Indices 0 and 1 are absent from every cheat list
consulted. Both were pressed on the real title screen:

* `Up,Down,Up,Right` → completion breakpoint hit, `r1=0`, `r2=4`.
* `Left,Right,Left` → completion breakpoint hit, `r1=1`, `r2=3`.
* Neither opens the cheat menu nor unlocks the `BONUS` items; their gameplay
  effect remains unknown (§8). These are the "undocumented combinations"
  required by §0.2 for a button-code system.

**Bounds proven by rejection.** A near-miss of the published code,
`B,A,Up,A,Select,Select` (one mask changed), was pressed on the title screen with
the breakpoint armed: **no completion hit**, and the title screen simply timed out
to DEMO. This proves the matcher uses exact per-frame masks and that no additional
sequence sharing the `BADASS` prefix is accepted.

**Codes from other platforms were checked, not assumed:** none of the PS2/Xbox/GC
sequences appear as `u16` mask arrays in this image.

## 7. Validation evidence

* **Observed (emulator):** title → DEMO flow; the `EXTRAS` cheat menu with two
  checkbox items after `BADASS`; D-pad moves the orange highlight; the `OPTIONS`
  screen (`SFX/MUSIC/BONUS/HIGH SCORES/CREDITS`); `BONUS` screen with two padlocked
  items (`SNOWBOARDING`, `MOTO X`); `SELECT SLOT`; in-game HUD/cutscenes; legal
  screen. Screenshots: `/tmp/ff4flameon/montage_bc_badass.png`,
  `montage_wa.png`, `cm_full_zoom.png`.
* **Observed (debugger, ground truth):** `b 0x08073EE0` hit for each of the three
  sequences, with `r1` = 0/1/2 (code index), `r2` = 4/3/6 (length), final `r5` =
  `0x10`, `0x20`, `0x04` (last button mask), manager object `0x0200D074` in EWRAM.
  No hit for the novel near-miss. This is the RAM/register proof that all three
  codes are accepted and that one near-miss is rejected.
* **Derived (static):** the `u16` mask arrays at `0x0808ACC8`–`0x0808ACED`, the
  three-entry pointer list at `0x080188DC`, the `AddSequence`/`StepMatch`/
  `Completion` call chain, and the exact-match semantics described in §5.
* **Inferred:** the `EXTRAS` menu name and `OFF`/`ON` labels come from the adjacent
  ASCII text bank, but no `OFF`→`ON` visual transition was observed when pressing
  A/B/L/R on the two items — the effect of selecting them is unresolved.

## 8. Unknowns

1. What indices 0 and 1 actually change. They are accepted by the validator but
   produce no visible title-screen change, no cheat menu, and no BONUS unlock with
   a clean save. They may be developer leftovers or set a flag consumed later in
   gameplay. A save-bit unlock was checked and ruled out for the BONUS items.
2. Whether the two `GIMME ...` checkboxes are toggles or one-shot grants: the yellow
   ✗ glyphs are byte-identical before and after A/B/L/R presses (pixel checksum of
   the yellow-pixel set unchanged). No `OFF`→`ON` text was ever rendered.
3. The profiling / `Player Debug Screen` strings (`0x080895F4`–`0x080897D0`) are
   present but no reachable route to them was found: no button sequence registers
   them, and no menu entry leads there. Classified as dead/stripped developer UI in
   this build.
4. The in-game pause screen (`PAUSED/RESUME/QUIT` strings) was not reached with
   Start or Select during the tutorial section; this is a UI-state observation,
   not a claim that no pause menu exists.
5. Save-file persistence: an EEPROM `.sav` (512 bytes) is created in the ROM folder;
   part of it was written by earlier experiments. Code 0/1 tests were repeated
   after deleting the `.sav` to avoid a stale flag producing a false positive.

## 9. Tooling

* `md5sum`, `sha1sum`, `sha256sum`, `file`, `xxd`, `strings -t x`
* Python 3 + `struct` scans for pointer literals and `u16` key-mask arrays
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
* `mgba -3` under `Xvfb :315` + `openbox`; `xdotool` XTEST input; `import -window root`
* `mgba -d` command-line debugger via a Python `pty`; `b 0x08073EE0` / `c`
* Pillow pixel sampling to detect the transient title screen for reproducible input
* `ssdiff.py` (mGBA `.ss1` `gbAs` zlib chunk diff) — used during triage; noisy
  because of background animation, so the debugger was used for the final claims

No ROM or copyrighted assets are redistributed here; only hashes, addresses,
algorithms and tool scripts are published.

## 10. Legal note

Analysis was performed on a legally obtained ROM for research. No game assets,
ROM bytes beyond a few literal addresses, or save data are included in this report.
