# Guilty Gear X: Advance Edition (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Guilty Gear X: Advance Edition.gba` |
| Size | 8,388,608 bytes (0x800000) |
| Header title | `GGXAE` |
| Game code / maker | `AGXE` / `BF` (Arc System Works / Sammy, EU rev 0) |
| `file(1)` | `Game Boy Advance ROM image: "GGXAE" (AGXEBF, Rev.00)` |
| MD5 | `509139bb43b0fa487056e6068c46ab70` |
| SHA-1 | `bb064410c57324b25de96d297338cc5e73262fe6` |
| SHA-256 | `4874e061e34556f97dc12927e807a3361245ac9100e00a14cf59b3e9527d3a27` |

Header check: entry word `0xEA00002E` → `0x080000C0` (stock crt0). A full-ROM scan for the
156-byte Nintendo logo found **exactly one** header, at file `0x0` — no multigame pack, no
appended trainer, no cracktro. Complement byte `0xBD=0x38` with checksum `0x0000` is a mild
"header was rebuilt" signal (common for EU releases) but no code patch was found.

## 2. Executive summary

The game has **one** developer-intended cheat system: a **5-button press sequence** entered on
the title ("PRESS START") screen. There is no password/code-entry screen, no hidden menu, and
no text alphabet to reverse. The entire accepted input set is a **hard-coded table of exactly
six 5-mask records** at ROM `0x0807A0A2`. All six match published lists; exhaustive static and
dynamic verification proves **no seventh accepted sequence exists** (§6b).

The validator (`0x0802D9D4`) copies the 60-byte table to the stack, compares it against a
5-entry button-history in the state struct, and returns `1 << code_index`. The caller
(`0x0802D038`) passes that bitmask to the flag setter `0x0802DAD0`, which ORs unlock bits into
`0x02000024` / `0x02000028`. Every code was entered in mGBA and its exact flag word read from a
savestate; character-select and OPTIONS-screen effects were also confirmed visually.

Two findings not present in the published lists:
1. The "Unlock Dizzy" code sets **two** flag bits (both Dizzy **and** Testament); the
   "Unlock Testament" code sets only one. Published pages describe these as independent.
2. Combining the Extra and GG-mode codes yields an all-32-variant-bit state
   (`0x02000024=0xFFFFFFFC`, `0x02000028=0x00000003`) that no published code describes.

Published console (PS2/DC) codes — `Down,Right,Right,Up[/Start]`, "Romantic"/"Misosoup",
`MJNKPNPN`, etc. — are **not** present and are rejected by the GBA build.

## 3. How to reproduce

* Emulator: mGBA SDL (`mgba -3`), `DISPLAY=:318`, `SDL_AUDIODRIVER=dummy`.
* Keymap verified in-game: `A=x`, `B=z`, `L=a`, `R=s`, `Start=Return`, `Select=BackSpace`,
  D-pad = arrow keys. Hold ~150–180 ms per press.
* Reach the title screen: boot → "Licensed by Nintendo" → Sammy logo → title with blinking
  `PRESS START` (≈6–10 s). Press `Start` for the main menu.
* Enter a code on the **title screen only** (not the menu, not in a match). Key masks are the
  standard active-high GBA values: `A=0x001 B=0x002 Select=0x004 Start=0x008 Right=0x010
  Left=0x020 Up=0x040 Down=0x080 R=0x100 L=0x200`.

| Effect | Buttons |
|---|---|
| Unlock Testament | Up, Down, Right, Left, A |
| Unlock Dizzy (+Testament) | Down, Down, R, L, R |
| Original Mode | A, B, A, L, L |
| Limit Release mode | L, R, A, A, A |
| All Extra-mode characters | Right, Down, Left, R, R |
| All GG-mode characters | Left, Down, Right, L, L |

Save a savestate on the title (`Shift+F1`), enter a code, save another (`Shift+F2`), then
diff the zlib `gbAs` chunk of the `.ssN` PNGs (§9). Flags appear at state offset `0x21024`
(→ EWRAM `0x02000024`) and `0x21028`.

## 4. Address map

| Item | File offset | ROM / RAM address | Notes |
|---|---|---|---|
| Button-code table | `0x7A0A2` | `0x0807A0A2` | 6 × 5 `u16` active-high masks, 60 bytes |
| Pointer to table | `0x2DA6C` | `0x0802DA6C` | literal `0x0807A0A2` |
| Validator | `0x2D9D4` | `0x0802D9D4` | Thumb; returns `1 << index` |
| Validator caller | `0x2D038` | `0x0802D038` | BL validator; BL flag-setter at `0x2D04A` |
| Flag setter | `0x2DAD0` | `0x0802DAD0` | maps return bit → unlock bits |
| Global state pointer | — | `0x03001600` | holds `0x02000000` |
| Unlock flags A | — | `0x02000024` | `u32` |
| Unlock flags B | — | `0x02000028` | `u32` |
| Character-name tables | `0x1103A2`, `0x11275B` | `0x081103A2`, `0x0811275B` | ASCII, `@`/`~` as space glyph |
| OPTIONS text bank | `0x1126A8` | `0x081126A8` | ASCII with `@`/`~` separators |
| Secondary text bank | `0x115A40` | `0x08115A40` | UTF-16LE; contains `LIMITED@RELEASE`, `ORIGINAL@MODE` |

mGBA savestate layout (4 MiB-style 397,312-byte state; identical here): IWRAM at file
`0x19000`, EWRAM at `0x21000`. `0x03001600` maps to file `0x1A600`.

## 5. Algorithm

Precise pseudocode of `0x0802D9D4` (arguments: `r0` = controller/state object, `r1` = current
key mask):

```
key = r1 & 0xFFFF
r4 = *(u32 *)(arg0 + 0x0C)              // internal history/counter struct
memcpy(stack, 0x0807A0A2, 60)           // 6 codes × 5 u16
counter = (counter + 1) % 180           // at r4+0x04

// append key to first empty slot of the 10-slot history at r4+0x12
i = 0
while (history[i] != 0 && i < 10) i++
history[i] = key

r8 = 0                                  // total matched presses (cumulative)
for code = 0 .. 5:
    exp = &stack[code * 10]
    if history[0] == exp[0]:
        r8++
        for j = 1 .. 4:
            if history[j] != exp[j]: break
            r8++
    if r8 == 5:
        clear history slots 0..9 and counter     // r4+0x12 .. r4+0x24
        return 1 << code
return 0
```

Because all six codes have **distinct first presses** (`Up, Down, A, L, Right, Left`), the
cumulative `r8` counter can only reach 5 when one single code matches completely — no spurious
accepts. The validator is invoked only by the title-screen handler; the same sequence on the
main menu or OPTIONS screen produces no flag change (tested).

Flag setter `0x0802DAD0`, with `state = *(void**)0x03001600` (= `0x02000000`):

```
if (ret & 0x01) state->flagsA |= 0x00000001          // Testament
if (ret & 0x02) state->flagsA |= 0x00000003          // Dizzy  (also Testament!)
if (ret & 0x04) state->flagsB |= 0x00000008          // Original Mode
if (ret & 0x08) state->flagsB |= 0x00000004          // Limit Release
if (ret & 0x10) for b in  2..17: setbit(state->flagsA, b)   // Extra modes (16 chars)
if (ret & 0x20) for b in 18..33: setbit(state->flagsA/B, b) // GG modes (16 chars)
```

## 6. Tables

### 6.1 Full code table (ROM `0x0807A0A2`)

| idx | masks (u16 LE) | Buttons | Return | Published effect | Observed flag effect |
|---:|---|---|---|---|---|
| 0 | 0040 0080 0010 0020 0001 | Up, Down, Right, Left, A | `0x01` | Unlock Testament | `flagsA |= 0x00000001` |
| 1 | 0080 0080 0100 0200 0100 | Down, Down, R, L, R | `0x02` | Unlock Dizzy | `flagsA |= 0x00000003` (**both**) |
| 2 | 0001 0002 0001 0200 0200 | A, B, A, L, L | `0x04` | Original Mode | `flagsB |= 0x00000008` |
| 3 | 0200 0100 0001 0001 0001 | L, R, A, A, A | `0x08` | Limit Release | `flagsB |= 0x00000004` |
| 4 | 0010 0080 0020 0100 0100 | Right, Down, Left, R, R | `0x10` | All Extra chars | `flagsA |= 0x0003FFFC` (bits 2–17) |
| 5 | 0020 0080 0010 0200 0200 | Left, Down, Right, L, L | `0x20` | All GG chars | `flagsA |= 0xFFFC0000`, `flagsB |= 0x00000003` (bits 18–33) |

Terminator: `0x0000` at `0x0807A0DE`. Exactly six records; `memcpy` length 60 bytes leaves no
room for a seventh.

### 6.2 Flag-bit map

| Bits | Meaning | Set by |
|---|---|---|
| `flagsA.0` | Testament unlocked | idx 0, idx 1 |
| `flagsA.1` | Dizzy unlocked | idx 1 |
| `flagsA.2..17` | Extra mode for 16 characters | idx 4 |
| `flagsA.18..31` + `flagsB.0..1` | GG mode for 16 characters | idx 5 |
| `flagsB.2` | Limit Release enabled | idx 3 |
| `flagsB.3` | Original Mode enabled | idx 2 |

## 6b. Enumeration

**Space definition.** The system is a pure lookup, not a checksum algorithm. Alphabet = 10
single-button masks; length = exactly 5 presses; table size = 6 records. Number of
representable inputs = `10^5 = 100,000`; accepted set = **6**. Field widths are not applicable
(no payload/checksum bits); the only state is the 34-bit unlock bitfield above.

**Exhaustiveness / bounded negative.** The accepted set is closed and fully characterised:
* the validator's `memcpy` length (60 bytes) and loop bound (`code <= 5`) fix the table at six
  entries (derived from disassembly, `0x0802D9D4`);
* the six entries were dumped byte-for-byte and each matched a published code literally
  (observed);
* a ROM-wide scan for other 5-`u16` button-mask tables found no second candidate driven by a
  validator (the `0x0807A0A2` pointer is the only literal into that data region);
* all six codes were entered and RAM-verified; five distinct out-of-set inputs were rejected.

Consequently **no unpublished accepted code exists in this build** — §0.2's "mint an
unpublished code" cannot be satisfied here, and that is a proven statement about this closed
6-entry space rather than an untested gap. The nearest novel results obtained are:

1. **Undocumented effect of a published code** (no published list states this): the Dizzy code
   `Down,Down,R,L,R` writes `0x00000003` to `0x02000024`, unlocking Dizzy **and** Testament;
   the Testament code writes only `0x00000001`. Observed in RAM and in character select (the
   portrait grid gains the two hidden fighters).
2. **Novel combined state**: entering `Right,Down,Left,R,R` then `Left,Down,Right,L,L` produces
   `flagsA=0xFFFFFFFC, flagsB=0x00000003` — all 16 Extra **and** all 16 GG-mode variants at once,
   a combination no single published code yields. RAM-verified from savestate slot 2.
3. **Unadvertised context restriction** (bounded negative): the same five presses on the main
   menu or OPTIONS screen leave both flags at `0x00000000`.

**Bounds proven by rejection** (each from a clean title savestate, flags read after):

| Test input | `flagsA` / `flagsB` | Result |
|---|---|---|
| Up + Dizzy code (6 presses, filler first) | `0 / 0` | rejected — no sliding-window tolerance |
| Dizzy with last press changed to Up | `0 / 0` | rejected — exact mask match required |
| Dizzy truncated to 4 presses | `0 / 0` | rejected — length must be 5 |
| Up × 5 (not in table) | `0 / 0` | rejected |
| PS2 `Down,Right,Right,Up` | `0 / 0` | rejected — console code |
| DC `Down,Right,Right,Up,Start` | `0 / 0` | rejected — console code |
| Dizzy code on main menu / OPTIONS | `0 / 0` | rejected — title-screen only |

## 7. Validation evidence

* **Observed** (emulator): title/menu/OPTIONS/character-select/in-match/pause screens walked and
  screenshotted; all six codes set the predicted RAM words (savestate diffs); character-select
  portraits expand after the Dizzy code; `LIMITED RELEASE` and `ORIGINAL MODE` ON/OFF toggles
  appear in GAME OPTIONS after their codes; every rejection test above left flags at zero.
* **Derived** (disassembly): table contents and 60-byte length; validator matching loop and
  `1<<index` return; flag-setter bit mapping; global pointer `0x03001600 → 0x02000000`.
* **Inferred**: bit-label semantics (which of `flagsA.0/.1` is Dizzy vs Testament) are assigned
  from the published code descriptions plus the setter's overlap; the overlap itself is observed.

No prompt-injection or instruction-like content was found in fetched web pages or ROM strings;
fetched pages were treated as data.

## 8. Unknowns

* Which of `flagsA.0`/`flagsA.1` is read by which character-select slot was not traced to the
  exact renderer branch (the dual-set behaviour is observed, the per-bit reader is not).
* The 34th and higher flag bits beyond those listed are unused by any code; no hidden 7th code
  was found that sets them.
* `MESSAGE TEST` / `SIGNAL` / `CHARACTER COPY` / `COMMUNICATION` strings exist in a secondary
  text bank but were not reachable from the walked menus (no screen rendered them); they appear
  to be unused/localisation leftovers, not a hidden menu.
* Save-file unlocks (Arcade/Survival Daredevil clears) are gameplay progress, not button codes,
  and were not brute-forced (out of scope).

## 9. Tooling

* `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for the
  validator and callers.
* Python/`struct` scans for literal pointers, BL targets (`F000/F800` halfword pattern), and
  button-mask runs.
* `ssdiff.py` — parses mGBA `.ssN` PNGs, `zlib.decompress`es the `gbAs` chunk, and diffs the
  397,312-byte state (IWRAM `0x19000`, EWRAM `0x21000`).
* `gx.py` / `test_codes.py` — xdotool input on `DISPLAY=:318` with dynamic window geometry,
  automated code entry and flag reads.
* Screenshots retained in `/tmp/opencode/ggx/shots/` (not redistributed with this report).

**Legal note:** no ROM bytes or copyrighted assets are reproduced here; only addresses, hashes,
algorithms and original observations are published.
