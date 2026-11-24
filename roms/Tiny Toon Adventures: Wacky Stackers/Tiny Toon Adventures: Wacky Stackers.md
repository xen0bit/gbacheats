# Tiny Toon Adventures: Wacky Stackers (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Tiny Toon Adventures: Wacky Stackers.gba` (same folder as this report) |
| Size | 4,194,304 bytes (4 MiB) |
| Header title | `TTA-WACKY` |
| Game code / maker | `AWSE` / `5Z` |
| Version / fixed byte | `0x00` / `0x96` |
| Entry word | `0xEA00002E` → `0x080000C0` (stock crt0; no cracktro/trainer) |
| MD5 | `ed37a03ef4b1df0bee663751cc021aa2` |
| SHA-1 | `fd9d10006bd29945ac16c6f88608a27e15f8f7da` |
| SHA-256 | `f8d9603ab28d4f9fd7bb1ee40dbbed65fa176295145e1f9023fa9466c9ba41d1` |

Analysed build is the exact file with the hashes above; all addresses below are for this image.

## 2. Executive summary

The game has **one developer-intended cheat**: a title-screen button sequence
`Up / Down / Left / Right / R` that makes the text `01-10-05` appear in the
top-left corner. It is documented in the 3rd party cheat index guide by Shy Ranger (§X,
"TITLE SCREEN CODE"). The sequence is **not** a password/checksum system: it is
a 5-entry table of raw button masks compared against the freshly-pressed button
mask with exact equality. The sole effect is drawing a fixed ASCII string; no
game state, flag, unlock or level is changed. `01-10-05` is a hard-coded result
string at `0x080308E0`, not a computed value, and its meaning remains unknown.

The button masks use a **nonstandard remapping** performed by the game's key
reader at `0x08000F7C`: `R` is bit 2 (`0x004`), not the GBA-standard `0x100`.
This is why a naive search for the published sequence fails. The table was
found by scanning for the first four published masks (`40 00 80 00 20 00 10 00`)
at `0x08020A8C`.

Enumeration (§6b) proves there is exactly **one** such table in the entire 4 MiB
image, and the validator is a generic table-driven matcher. A novel sequence
(`A, B, R, L, Right`) patched into the RAM table was accepted by the game,
proving the accept path is fully understood; the same sequence typed with
unmodified ROM data is correctly rejected.

No password screen, debug menu, level select, cheat alphabet or hidden unlock
exists in this build. The only alphabet in the ROM (`0x080221FC`,
`ABCDEFGHIJKLMNOPQRSTUVWXYZ! `) is the multiplayer **name-entry** character set,
not a validator input (§16.2b).

## 3. How to reproduce

* Emulator: mGBA 0.10.5, `Xvfb :318`, `SDL_AUDIODRIVER=dummy`, window focus via
  `xdotool windowfocus` + XTEST key events. Keymap A=`x`, B=`z`, L=`a`, R=`s`,
  Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold ~100–140 ms per press.
* Boot the ROM, wait through the legal notice / Warner Bros. / Conspiracy /
  Warthog logo screens until the "Tiny Toon Adventures: Wacky Stackers" title
  screen with the rainbow circle and "PRESS START".
* Press **Up, Down, Left, Right, R** in order (one at a time).
* Result: `01-10-05` appears in the top-left (screenshot `title_after_R.png`,
  `test_published.png`). It persists while the title screen is displayed.
* Negative: press any other 5-button combination, or only 4 presses, or use
  Select instead of R — nothing appears (`test_novel.png`, `test_short4.png`,
  `test_select5.png`, `test_reversed.png`).

Screenshots and scripts were in `/tmp/wackystackers/`.

## 4. Address map

| Address | Meaning | Evidence |
|---|---|---|
| `0x08000F7C` | Key reader: `~KEYINPUT` → custom 10-bit mask (mapping in §6) | Derived (disassembly) |
| `0x08002F70` | Input processor: debounce/repeat, produces "newly pressed" mask in `r2` | Derived |
| `0x08002FF0`–`0x0800301E` | Button-code validator (the `cmp r2,r0` at `0x0800300E`) | Derived |
| `0x08030D4` | Initialiser: `memset(0x030002D0,0,44)`, then `memcpy(0x03000220, 0x08020A84, 24)` at `0x0803106` | Derived |
| `0x08020A84` | ROM code table: `{u32 5, u32 0, u16[5] {0x40,0x80,0x20,0x10,0x04}}` | Derived |
| `0x080308E0` | ASCII result string `"01-10-05\0"` | Observed (bytes) + in-game |
| `0x0809402` | Title loop calls input processor `0x08002F70` | Derived |
| `0x0809434`–`0x0809454` | Title loop checks `index == count`, draws string at (0,16), resets index | Derived + observed |
| `0x080221FC` | Multiplayer name-entry alphabet `ABCDEFGHIJKLMNOPQRSTUVWXYZ! ` | Derived |
| `0x03000220` | IWRAM code struct: `+0` count (5), `+4` progress index, `+8` u16 sequence[5] | Observed via savestate patch at offset `0x19220` |
| `0x030002D0` | IWRAM key state (10 buttons × 4-byte records from `+4`) | Derived |
| `0x04000130` | KEYINPUT register | Derived |

File offset ↔ ROM address: `0x08000000 + file_offset`. IWRAM in mGBA `.ss1`
states starts at raw offset `0x19000` (4 MiB ROM), so `0x03000220` is at
`0x19220` — confirmed by locating the exact struct bytes in the decompressed
`gbAs` chunk.

## 5. Algorithm

Key reader (`0x08000F7C`), from `~KEYINPUT`:

```
r2 = (~KEY & 0x3C0) >> 6            # bits 6..9 of active-high mask
r2 &= 0b1100                       # keep original bits 8,9 (R,L) -> bits 2,3
r3 = ~KEY & 0xFF                   # bits 0..7
r0 = r3 & ~0b1100                  # A,B,Right,Left,Up,Down
r1 = (r3 & 0b1100) << 6            # Select,Start -> bits 8,9
return r0 | r1 | r2
```

Validator (`0x08002FF4`), operating on the struct at `0x03000220`:

```
if newly_pressed == 0: return
idx = struct[4]; cnt = struct[0]        # cnt = 5
if idx == cnt: idx = 0                 # wrap/re-arm
expected = u16 struct[8 + idx*2]
if newly_pressed == expected: idx += 1
else: idx = 0                          # exact match, no tolerance
struct[4] = idx
```

Success path in the title loop (`0x0809434`):

```
if struct[4] == struct[0] and not already_drawn:
    draw_text(0, "01-10-05", 8, 16)    # 0x080DA58
    struct[4] = 0                      # re-arm
```

`newly_pressed` is edge-triggered with a per-button debounce/repeat filter
(`0x08002F70`): a button is removed from the mask while it is held past the
repeat delay; only the transition frame survives to the validator. Because the
comparison is `==` (not `&`), the pressed mask must equal the expected mask
exactly — any extra button in the same frame would fail (Derived from
`0x0800300E`; see §8 for the caveat on the simultaneous-press test).

## 6. Tables

**Custom button masks** (bit → button):

| bit | mask | button | bit | mask | button |
|---:|---:|---|---:|---:|---|
| 0 | `0x001` | A | 5 | `0x020` | Left |
| 1 | `0x002` | B | 6 | `0x040` | Up |
| 2 | `0x004` | R | 7 | `0x080` | Down |
| 3 | `0x008` | L | 8 | `0x100` | Select |
| 4 | `0x010` | Right | 9 | `0x200` | Start |

**ROM code table at `0x08020A84`** (24 bytes):

| offset | value | meaning |
|---|---|---|
| `0x08020A84` | `0x00000005` | count = 5 |
| `0x08020A88` | `0x00000000` | zero/unused |
| `0x08020A8C` | `0x0040` | Up |
| `0x08020A8E` | `0x0080` | Down |
| `0x08020A90` | `0x0020` | Left |
| `0x08020A92` | `0x0010` | Right |
| `0x08020A94` | `0x0004` | R |
| `0x08020A96`–`0x08020A9B` | `0` | padding |

**Result string**: `"01-10-05"` at `0x080308E0` (fixed; never recomputed).

**Published-code verification**: 3rd party cheat index guide (Shy Ranger, 2003, recovered via
Wayback) lists exactly this one sequence. It was verified literally against
`0x08020A8C` and accepted in the emulator. No other published cheat list
(3rd party cheat indexes have none for this SKU) was found.

## 6b. Enumeration

**Space definition.** A code is a sequence of exactly `count = 5` button masks,
each drawn from the 10-button alphabet in §6. With retail ROM data the table is
fixed, so the representable space is `10^5 = 100,000` sequences and the accepted
set is **exactly 1**:

```
Up, Down, Left, Right, R     = 40 80 20 10 04   (ROM 0x08020A8C)
```

There is no checksum, no field encoding, no reserved bit and no length variant:
the validator is a single equality per position with a wrap at `index == count`.
A full-ROM struct scan (`scan_tables.py`: `{u32 count in 2..16, u32 0, u16
seq[count]}` with every entry a valid key mask) found **exactly one** table —
`0x08020A84`. Counts of other code surfaces: ASCII password strings = 0
(full `strings -n 4` sweep; only `01-10-05` in the debug-text region
`0x08030700`–`0x08031000`); cheat/debug keyword hits = 2, both the
`ENTERTAINMENT` text in logo banks; debug menus reachable by screen walk = 0.

**Novel code, minted and accepted.** The validator was proved generic by
patching the RAM sequence in a title-screen savestate (raw offset `0x19220` =
IWRAM `0x03000228`) from `40 80 20 10 04` to:

```
A, B, R, L, Right   = 01 02 04 08 10
```

This combination appears in **no** published list. The patched state was loaded
in mGBA and the five buttons were pressed: the game accepted it and displayed
`01-10-05` (`novel_accepted.png`, byte-identical result to the published code).
**Caveat:** this required a savestate/RAM patch, not retail input; the retail
ROM offers no way to change the table, so this is a proof of the validator
model, not a new player-usable code.

**Undocumented retail combination pressed.** `Left, Up, Down, B, R` was typed at
the title screen: no text appeared (`test_novel.png`). This is the required
"press an undocumented combination" test (§0.2) for a button-code system.

**Bounds proved by rejection** (all from the clean-title savestate, retail
input, no patches):

| Test | Sequence | Result |
|---|---|---|
| Correct code | Up Down Left Right R | `01-10-05` displayed |
| Novel 5-press | Left Up Down B R | rejected — no text |
| Reversed | R Right Left Down Up | rejected — no text |
| Wrong length (4) | Up Down Left Right | rejected — no text |
| Wrong 5th button | Up Down Left Right Select | rejected — no text |

These bound the system to a fixed 5-slot exact-match table: a different symbol,
a different order, a missing symbol or a shorter sequence all fail.

## 7. Validation evidence

* **Observed** — `01-10-05` appears at the top-left after the published sequence
  (`title_after_R.png`, `test_published.png`) and after the patched novel
  sequence (`novel_accepted.png`); no text appears for all four rejection tests.
  Screenshots are byte-compared by MD5 to distinguish the two outcomes.
* **Observed** — the exact 24-byte struct located in the decompressed mGBA
  savestate at raw offset `0x19220`, confirming the ROM→IWRAM copy target.
* **Derived** — key remapping (`0x08000F7C`), validator (`0x08002FF4`),
  initialiser (`0x08030D4`/`0x0803106`), display check (`0x0809434`), all from
  `objdump -M force-thumb` and cross-checks with literal/pointer scans.
* **Derived** — single-table result from a whole-ROM struct scan.
* **Inferred** — `01-10-05` is a build/version tag of unknown meaning; the FAQ
  author likewise could not identify it.

Screen walk (observed): legal notice → logo sequence → title → Game Type →
Survival Difficulty → Survival gameplay → pause menu (`CONTINUE`/`QUIT`) →
game over → Puzzle "2/5/8 CHALLENGES" → puzzle intro cutscene. The FAQ also
documents 1P v COM, Multiplayer setup/name entry, the continue screen, credits
and ending movie; none of these exposed a password or debug entry point.

Web content was treated as data only; no instructions found in fetched pages or
ROM strings were acted upon. No prompt-injection payload was encountered.

## 8. Unknowns

* The semantic meaning of `01-10-05` is unknown (likely a build/date tag).
* A truly same-frame simultaneous extra-button test was inconclusive: with
  XTEST, `x` then `Up` were registered in different frames, so the code still
  succeeded (the first `A` press was consumed as a separate rejected press).
  Exact-match semantics are therefore **Derived** from `cmp r2, r0`, not
  **Observed** for same-frame multi-press.
* No GDB-stub session was usable: attaching stopped the core and the stub
  became unresponsive, so all dynamic RAM evidence came from savestate diffs
  and savestate patching (§16.13 method) instead.
* The multiplayer name-entry buffer was not exhaustively proven to have no
  validator consumer; its only observed use is identifying players' screens,
  and its alphabet is referenced from the text-drawing routines at
  `0x0800D194`/`0x0800D3C0`. A full xref/consumer count was not completed.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings`, `grep`
* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`
* Python scripts in `/tmp/wackystackers/`:
  `scan_buttons.py` (button-mask encodings), `dump.py` (hex/u16 dump),
  `xreffast.py` (u32 pointers, Thumb BL / LDR-literal / ARM LDR-literal),
  `litref.py`, `ramref.py`, `scan_tables.py` (whole-ROM struct scan),
  `key.py` (XTEST input helper), `testcode.py` (savestate test harness),
  `patch_state.py` (PNG/gbAs zlib savestate patcher).
* mGBA 0.10.5 with `-3` scaling; Xvfb `:318` + openbox; `SDL_AUDIODRIVER=dummy`;
  `xdotool` for input, `scrot` for screenshots.
* No ROM or copyrighted assets are redistributed in this report.
