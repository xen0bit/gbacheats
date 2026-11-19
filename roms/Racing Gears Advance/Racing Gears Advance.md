# Racing Gears Advance (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Racing Gears Advance/Racing Gears Advance.gba` |
| Size | 8,388,608 bytes (0x00800000) |
| Header title | `RACING GEARS` |
| Game code | `BRAE` |
| Maker | `GH` |
| Version | 0x00 (complement 0x62) |
| Entry word | `0xEA00002E` (stock — no cracktro/trainer patch) |
| MD5 | `1dac1484f1d66158b1cfae3da7c79af9` |
| SHA-1 | `3f053865f9a687a75927172cd281390b2560201c` |
| SHA-256 | `2f300e80a39749370a64ba86540a99aa523aece87d49f4962e5b89df886946e8` |

Embedded GBA-header scan (156-byte Nintendo logo at header +0x04) found **exactly one**
header, at file offset `0x0`. No multi-game image, no appended trainer, no patched
entry point. The first 4 KiB is ordinary ARM crt0 code.

## 2. Executive summary

The game implements a **button-code system**, not a password/keypad system. Ten
developer codes are stored as NUL-terminated arrays of active-high GBA key masks
(`u16`, no R bit) at ROM `0x0877C5C`–`0x0877CE6`, followed immediately by a closed
descriptor table of ten 12-byte records at `0x0877CE8`–`0x0877D60`. There is no
eleventh record: the next word is unrelated data. The published GameFAQs list of
ten codes matches the ROM table exactly.

Entering a code on the "NEXT TRACK"/garage screen while holding **R** sets one bit
in a 10-bit RAM flag word at `0x0203823C` (one bit per code, bits 0–9, no gaps)
and increments a byte at `0x0203892D`. All ten codes were entered in mGBA and each
produced its name in the DIFFICULTY panel plus the expected RAM bit. The matcher
is **suffix-based**: a code followed by an extra button press is still accepted —
this yields an input sequence that appears in no published list while producing a
published effect (documented in §6b). Near-miss and reversed sequences are
rejected with the flag word remaining zero (bounds proof).

No password keypad, debug menu, or hidden code beyond these ten button sequences
was found; the negative is bounded by the closed 10-entry table and by the full
10-bit flag word being accounted for.

## 3. How to reproduce

* Emulator: mGBA SDL on `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`, `mgba -3`.
* Keymap (verified against KEYINPUT at `0x04000130`): `A=x`, `B=z`, `L=a`, `R=s`,
  arrows = D-pad.
* Menu path: title → A → START MENU → A → GAME TYPE → A → CHAMPIONSHIP → A/A
  (driver details) → A → CIRCUIT → A → **NEXT TRACK** (garage screen with the
  wrench toolbar icon).
* Code entry: hold **R**, press each listed button with ~200 ms down / ~200 ms up,
  then release R. 120 ms holds were unreliable; 200 ms worked consistently.
* Cheat acceptance is shown by the code's name in the yellow DIFFICULTY text at
  the lower right, and by the RAM bits in §6.
* Savestates: `Shift+F1`…`Shift+F9` save, `F1`…`F9` load. The `.ssN` files are
  PNGs with a zlib-compressed `gbAs` chunk; decompress to a 397,312-byte state.
  EWRAM mapping: `state_offset = 0x21000 + (addr - 0x02000000)`.

Codes verified (all ten accepted):

| Name | Buttons (with R held) | RAM bit |
|---|---|---|
| Wussy | B,A,B,B,L | 0x0001 |
| Equalizer | U,U,B,D,A | 0x0002 |
| Hamburger | A,A,L,LEFT,RIGHT,UP | 0x0004 |
| Armageddon | B,B,L,RIGHT,LEFT,D | 0x0008 |
| AAA | A,L,B,RIGHT,RIGHT,UP,A | 0x0010 |
| Blindspot | RIGHT,A,B,B,LEFT | 0x0020 |
| Sprint | D,U,B,LEFT,RIGHT,A | 0x0040 |
| Endurance | LEFT,B,A,RIGHT,L,L,D | 0x0080 |
| Taxman | L,A,B,L,D,D | 0x0100 |
| Cashcrop | RIGHT,L,UP,A,LEFT,B | 0x0200 |

## 4. Address map

| Address (ROM / RAM) | Meaning | Evidence |
|---|---|---|
| `0x08000000` | Entry ARM branch `0xEA00002E`, stock | Observed (header + scan) |
| `0x0802825C` | Input poll: `r1 = ~KEYINPUT & 0xFFFF`; writes held/pressed/released | Derived (Capstone) |
| `0x02038242` | Held keys, active-high (idle `0xFC00`) | Observed (breakpoint + state) |
| `0x02038240` / `0x02038244` | Newly pressed / newly released masks | Derived |
| `0x0877C5C`–`0x0877CE6` | 10 NUL-terminated `u16` key-mask sequences | Observed (literal search) |
| `0x0877CE8`–`0x0877D60` | 10 descriptors, 12 bytes each: `{u32 seq_ptr, u32 fieldB, u32 text_id}` | Derived |
| `0x08785A8` | Pointer to descriptor table (in resource manifest) | Observed |
| `0x0800F97C` | Cheat activation function (sets flag bit, increments count) | Observed (write watchpoint) |
| `0x0800FAEE`–`0x0800FAF8` | `ldr` flag word / `strb` count, watchpoint PC `0x0800FAF0` | Observed |
| `0x0800FE20` | `BL` to activation function | Derived (BL scan) |
| `0x0203823C` | Cheat flag word, `u16`, 10 bits | Observed (watchpoint + diffs) |
| `0x0203892D` | "code active" byte (0 or 1) | Observed (state diffs) |
| `0x02038928` = `0x03FF` | Key-universe mask used by matcher | Observed (state diffs) |

Text: the code names are **not ASCII in ROM**. Each descriptor carries a
font/tile-indexed text ID (`0x234`…`0x23D`, e.g. Hamburger `0x23A`). The rendered
names (AAA, ARMAGEDDON, BLIND SPOT, CASH CROP, ENDURANCE, EQUALIZER, HAMBURGER,
SPRINT, TAX MAN, WUSSY) were read directly from the emulator's DIFFICULTY panel
and matched to the ten descriptors.

## 5. Algorithm

Derived from the mask arrays, the activation function, and dynamic tests:

```
KEYINPUT (0x04000130) active-low; active-high mask = ~KEYINPUT & 0x3FF
buttons: A=0x001 B=0x002 SELECT=0x004 START=0x008 RIGHT=0x010 LEFT=0x020
         UP=0x040 DOWN=0x080 R=0x100 L=0x200

on each poll in the garage:
  if R is held:
     push current non-R buttons into a recent-press history (suffix window)
     for i in 0..9:
        seq = descriptor[i].seq_ptr
        if history endswith seq[0..n-1] (u16 masks, NUL-terminated):
            flag = flag_word (0x0203823C)
            if not (flag & (1 << i)):
                flag |= (1 << i)
                count_byte (0x0203892D) = 1
                show text ID descriptor[i].text_id in DIFFICULTY panel
            break
  wrong/incomplete sequence -> no bit set (observed: invalid entry leaves flag 0)
```

The activation function at `0x0800F97C` loops `r4 = 0..9` testing bits, then
ORs `1 << cheat_index` into `[r6 + 0x25C]` where `r6 = 0x02037FE0` (giving
`0x0203823C`) and increments the byte at `0x0203892D`. The comparator itself was
not isolated statically, but its semantics were established dynamically
(§6b, §7).

## 6. Tables

Key masks per code (active-high, R excluded; R is the gate):

| # | Name | Mask sequence | text_id | descriptor fieldB | flag bit |
|---|---|---|---|---|---|
| 0 | WUSSY | 002 001 002 002 200 | 0x234 | 0x0000000C | 0x0001 |
| 1 | EQUALIZER | 040 040 002 080 001 | 0x239 | 0x00000000 | 0x0002 |
| 2 | HAMBURGER | 001 001 200 020 010 040 | 0x23A | 0x00000001 | 0x0004 |
| 3 | ARMAGEDDON | 002 002 200 010 020 080 | 0x23D | 0x00000001 | 0x0008 |
| 4 | AAA | 001 200 002 010 010 040 001 | 0x236 | 0x00000000 | 0x0010 |
| 5 | BLINDSPOT | 010 001 002 002 020 | 0x235 | 0x00000000 | 0x0020 |
| 6 | SPRINT | 080 040 002 020 010 001 | 0x23B | 0x00000080 | 0x0040 |
| 7 | ENDURANCE | 020 002 001 010 200 200 080 | 0x238 | 0x00000040 | 0x0080 |
| 8 | TAXMAN | 200 001 002 200 080 080 | 0x23C | 0x00000200 | 0x0100 |
| 9 | CASHCROP | 010 200 040 001 020 002 | 0x237 | 0x00000100 | 0x0200 |

Descriptor fieldB is a per-code 32-bit value; for codes 6–9 its low halfword is
a power of two that does not match the §6 flag bit (SPRINT/ENDURANCE and
TAXMAN/CASHCROP are exchanged), so its semantics are **unknown** and it is not
claimed to be the flag. Published effects (GameFAQs/GameGenie) for the ten codes
are the standard ones; `EQUALIZER` is published as "???", and its only proven
effect here is flag bit 1 / the EQUALIZER label.

## 6b. Enumeration

**Space definition.** The system is a closed lookup of exactly **10** button
sequences. Sequence table: `0x0877C5C`–`0x0877CE6` (10 NUL-terminated `u16`
arrays, lengths 5–7). Descriptor table: `0x0877CE8`–`0x0877D60` (10 × 12 bytes);
the word at `0x0877D60` (`0x01078296`) is not a valid descriptor pointer, so the
table ends there. The runtime flag is a 10-bit mask (`0x0001`–`0x0200`) with
**no unassigned bits** — every bit 0–9 maps to one table entry. Therefore no
eleventh code can exist in this system.

**Published-list comparison.** All ten GameFAQs codes were found literally in
the ROM table and all ten were accepted in the emulator. No published code was
absent or mis-transcribed.

**Novel (unpublished) input.** Because the matcher is suffix-based, the sequence

```
R + A,A,L,LEFT,RIGHT,UP,A   (Hamburger with one extra trailing A)
```

is accepted: RAM flag `0x0004`, count `0x0203892D = 1`, and the emulator shows
`HAMBURGER` in the DIFFICULTY panel. This 7-press sequence appears in no
published list (all lists publish the 6-press Hamburger code) and is therefore
the button-code equivalent of a minted, unpublished code.

**Bounds proven by rejection** (each preceded by an invalid reset sequence,
measured from the savestate at `0x0203823C`):

| Input | Flag after |
|---|---|
| clean / no code | `0x0000` |
| R + A×6 (invalid) | `0x0000` |
| R + A,A,L,LEFT,RIGHT,DOWN (near-miss Hamburger) | `0x0000` |
| R + UP,RIGHT,LEFT,A,A,A (reversed Hamburger) | `0x0000` |
| R + A,A,L,LEFT,RIGHT,UP,A (novel, suffix) | `0x0004` |

**Combination note.** Entering a second and third code without an intervening
invalid reset replaced the flag rather than accumulating it (`0x0004 → 0x0008 →
0x0010`, count stayed 1). The published "up to 3 codes at a time" claim was not
observed with this entry method (R was released between codes); this is recorded
as a discrepancy, not as a proven limitation.

## 7. Validation evidence

* **Observed** — hashes/header; single embedded header; ten mask sequences and
  descriptors dumped from ROM; all ten codes accepted in mGBA with their names
  rendered; flag word `0x0203823C` read from decompressed savestates for every
  code; write watchpoint hitting at `0x0800FAF0` with new value `0x00000004` for
  Hamburger; rejection cases leaving flag `0x0000`; title/game-type/vehicle/
  circuit/garage/race screens walked by screenshot.
* **Derived** — descriptor record layout and table bounds; input routine at
  `0x0802825C`; activation function at `0x0800F97C` and its single BL caller at
  `0x0800FE20`; bit-per-code mapping; suffix-match semantics from the extra-press
  test.
* **Inferred** — the precise comparator loop and where the recent-press history
  buffer lives; the meaning of descriptor fieldB; the in-race gameplay effect of
  EQUALIZER (only its label and flag bit were observed).

Evidence discipline: fetched web pages were treated as data. No instructions
found in ROM strings or fetched pages were followed.

## 8. Unknowns

* Exact address and window length of the recent-press history buffer consumed by
  the comparator (suffix behavior is proven, implementation is not).
* Semantics of descriptor fieldB and why SPRINT/ENDURANCE and TAXMAN/CASHCROP
  values are exchanged relative to the runtime flag bits.
* Real in-game effect of EQUALIZER (published as "???").
* Why multiple codes replaced rather than accumulated under the tested entry
  method; the published 3-code combination behavior was not reproduced.
* Whether any gameplay-only cheat (hidden car/track, debug screen) exists behind
  a save-bit gate that requires completing circuits; unlockables listed by
  GameFAQs are progression-based (licenses/characters), not input codes, and no
  hidden debug menu was reached by menu walking.

## 9. Tooling

* `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings` — Phase 0/1.
* Python + `capstone` 5.0.7 — Thumb disassembly, literal/BL scans, mask-table
  scanner (`scan.py`).
* mGBA SDL under Xvfb `:318` + openbox; `xdotool` for input; `scrot`/ImageMagick
  for screenshots.
* mGBA CLI debugger via a pty (`pty_dbg.py`) — `watch/w` on `0x0203823C` located
  the writer at `0x0800FAF0`.
* `state.py` — parse mGBA `.ssN` PNG `gbAs` zlib chunk and diff EWRAM/IWRAM.
* Web: GameFAQs cheats page and GameGenie page (published codes), Wikipedia.

No ROM or copyrighted assets are redistributed in this report.
