# Spyro Orange: The Cortex Conspiracy (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Spyro Orange: The Cortex Conspiracy.gba` |
| Size | 16,777,216 bytes (0x01000000) |
| Header title | `SPYRO ORANGE` |
| Game code | `BSTE` (region code E = Europe/PAL build, "Spyro Fusion") |
| Maker | `7D` |
| Version | 0x00; fixed byte 0x96; complement 0x2F; header checksum 0x0000 |
| Entry word | `0xEA00002E` (stock GBA branch to 0x080000C0) |
| MD5 | `6a496546576101291a97a93846f0d9dd` |
| SHA-1 | `e76783d027fb1cd6426bfe3d482c595b585e32ae` |
| SHA-256 | `66f015ab78f4065b5892faaf3f1d7fab4d2f387ba6fd6f183c7a568d22d67160` |

Two further GBA headers with title `XXXXXXXXXXXX` / code `XXXX` exist at file offsets `0xF6AE48` and `0xF8CC74`; both are link/multiboot stubs (no code strings, no code table), not separate games. `-3` mGBA 0.10.5, display `:319`, `SDL_AUDIODRIVER=dummy`.

## 2. Executive summary

The game has a genuine developer-intended cheat-code system, reached by holding **L+R at the "game mode" screen** (Story Mode / Party Mode / Trading Cards / Credits). The entry screen is a 31-symbol on-screen keyboard (`B C D F G H J K / L M N P Q R S T / V W X Y Z 0 1 2 / 3 4 5 6 7 8 9` — no vowels) with a 10-character buffer (9 dashes shown as placeholders).

The validator at **`0x080284BC`** is a straight-line chain of **exactly ten `strcmp` calls** (to `0x0803BD98`) against **ten 8-byte NUL-padded strings** at `0x0805F0B8`. There is **no checksum, no algorithm, no generator and no second format**. On a match it applies one of ten effects; every other input falls through to one shared `Invalid Code!` path. Two gem codes are additionally gated by a once-per-save-slot byte.

All ten ROM strings match the ten codes published by 3rd party cheat indexes exactly. **The accepted set is therefore provably closed at ten codes, all of which are published — no novel accepted code exists.** This is a bounded negative proved by counting the validator's comparisons and the table's entries, and by entering all ten (accepted) plus four out-of-set strings (rejected) in the emulator (§6b).

A separate dead leftover, `Prototype Build`, exists in the text bank but the mode menu is a four-item ring and never displays or reaches it. A published "hold L+R at power-on → Crash Party" boot combo was **not reproduced** in this PAL build under mGBA.

## 3. How to reproduce

1. Boot the ROM in mGBA with the GDB stub (`mgba -g -3 <rom>`). Default SDL keymap: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrows.
2. At the title (`Press Start`) press Start → *Select a Slot* → choose a slot → the four-item game-mode menu appears.
3. Hold **L+R** (`a`+`s`) together on that menu → code-entry keyboard.
4. Move the D-pad over glyphs, press **A** to append a character, **B** to backspace (B on an empty buffer exits). Navigate past the last glyph (`9`) to the bottom-right `A Select` cell and press **A** to submit. The result screen reads `You entered: / Code Accepted! / <effect>` or `Invalid Code!`; B returns to the mode menu.
5. Repeatable oracle (used for the evidence below): save a state at the code-entry screen (`Shift+F1`); on each run reload it (`F1`), submit any string, set a breakpoint at **`0x08028546`** (the first `strcmp` call site), and at the stop overwrite the stack buffer pointed to by `r0` with the desired string before continuing. The game's own validator then processes it. Breakpoint observed values: `PC=0x08028546`, `r0=0x03007D30` (input buffer), `r1=0x0805F0B8` (literal `SH33P`).

Codes tested verbatim in the ROM and entered through the oracle: `SH33P SP4RX SPYR0 P0RT4L G3MZ V1S10NS T4P10C4 S0YB34N V4N1LL4 B41S0KV` (all accepted) and `SHEEPXX SH33PX AAAAAAA 1234567` (all rejected).

## 4. Address map

| ROM address | Meaning |
|---|---|
| `0x0805F0B8`–`0x0805F107` | Code string table: ten records, 8 bytes each, NUL-padded |
| `0x080284BC` | Code validator entry (called with a UI object in `r0`) |
| `0x08028546`, `0x08028590`, `0x080285C0`, `0x080285F0`, `0x08028620`, `0x08028650`, `0x080286A4`, `0x08028710`, `0x08028758`, `0x080287A0` | The ten `BL strcmp` call sites, one per code (in this order) |
| `0x080287CC` | Shared failure path → `Invalid Code!` (text ID `0x080D2780`) |
| `0x0803BD98` | `strcmp` used by the validator |
| `0x0803BDF4` | byte-copy helper (`strcpy`-like) that copies the entered buffer to the validator's stack |
| `0x08014970` / `0x0801497C` | once-only flag get/set: byte at `save_record + 0x1DE + index` (index 0 = `V1S10NS`, 1 = `T4P10C4`) |
| `0x08014DD0` | add gems (`r1` = amount: 100 / 200) |
| `0x08007348` / `0x08007324` | card owned-check / card grant (`r1` = 80 for `S0YB34N`, 52 for `V4N1LL4`) |
| `0x0801B5F8` | show result dialog with a text ID |
| `0x08032E98`, `0x0802D18C` | resolve text ID → string; set dialog message |
| `0x080D277C` | table of pointers to code-system messages (`Code Accepted!`, `Invalid Code!`, …) |
| `0x080D3050`–`0x080D30C4` | menu text IDs: Press Start, Story Mode, Party Mode, Trading Cards, Credits, **Prototype Build**, View Cards, Trade Cards |
| `0x0200FB24` (mirror `0x0200CCA8`) | code-entry display buffer (`<chars><'-' padding>` + NUL) |
| `0x03007D30` | validator's stack copy of the entered string (seen at the breakpoint) |
| `0x04000130` | KEYINPUT (active low); idle `0x03FF`, L+R held `0x00FF` |

## 5. Algorithm

```
validate(ui_object):
    s = stack_copy(code_entry_buffer)          # 0x0803BDF4 -> 0x03007D30
    for (code, effect) in the 10 fixed pairs:  # strcmp at 0x0803BD98
        if strcmp(s, code) == 0:
            apply(effect)
            show("Code Accepted!")
            show(effect_message)               # or gems/card/once-only message
            return
    show("Invalid Code!")                      # single shared failure path
```

Effect dispatch (derived from disassembly and confirmed in-game):

* `SH33P` → `Sheep Mode Activated!`
* `SP4RX` → `Orange Mode Activated!` (entire palette turns orange)
* `SPYR0` → `Orange Spyro Mode Activated!`
* `P0RT4L` → `Purple Mode Activated!` (entire palette turns purple)
* `G3MZ` → `Gray Mode Activated!` (entire palette turns gray)
* `V1S10NS` → 100 gems, once per slot (flag index 0)
* `T4P10C4` → 200 gems, once per slot (flag index 1)
* `S0YB34N` → `You have received a hidden card!` (card 80)
* `V4N1LL4` → `You have received a hidden card!` (card 52)
* `B41S0KV` → `Sheep Flame Mode Activated!`

The four cosmetic modes are runtime effects that revert on reset (per the published guide and the absence of any save write in their branches).

No checksum, PRNG, XOR key, bit packing, alias table, length branch or second alphabet exists anywhere on this path. `strcmp` returns zero only on exact byte equality up to NUL, so the accepted language is precisely the ten literals.

## 6. Tables

Code string table at `0x0805F0B8`, 8-byte stride, 10 entries (bytes verified with `xxd`; all ten also found literally by offset):

| File offset | ROM address | Code | Effect |
|---|---|---|---|
| 0x5F0B8 | 0x0805F0B8 | `SH33P` | Sheep Mode |
| 0x5F0C0 | 0x0805F0C0 | `SP4RX` | Orange Mode |
| 0x5F0C8 | 0x0805F0C8 | `SPYR0` | Orange Spyro Mode |
| 0x5F0D0 | 0x0805F0D0 | `P0RT4L` | Purple Mode |
| 0x5F0D8 | 0x0805F0D8 | `G3MZ` | Gray Mode |
| 0x5F0E0 | 0x0805F0E0 | `V1S10NS` | 100 gems (once/slot) |
| 0x5F0E8 | 0x0805F0E8 | `T4P10C4` | 200 gems (once/slot) |
| 0x5F0F0 | 0x0805F0F0 | `S0YB34N` | hidden card 80 |
| 0x5F0F8 | 0x0805F0F8 | `V4N1LL4` | hidden card 52 |
| 0x5F100 | 0x0805F100 | `B41S0KV` | Sheep Flame Mode |

Entry alphabet (on-screen keyboard, read from the rendered screen and decoded against the font): `BCDFGHJKLMNPQRSTVWXYZ0123456789` — 31 symbols, no vowels. Buffer holds 10 characters; codes occupy 4–7.

## 6b. Enumeration

**Space definition.** Input surface = 31 symbols × up to 10 positions. The validator itself imposes no alphabet or length restriction: it is plain `strcmp` against a fixed table. The complete accepted set is therefore the ten 8-byte records above — **10 accepted values**, lengths 4 (`G3MZ`), 5 (`SH33P`, `SP4RX`, `SPYR0`), 6 (`P0RT4L`) and 7 (`V1S10NS`, `T4P10C4`, `S0YB34N`, `V4N1LL4`, `B41S0KV`). There are no unused payload bits, reserved bits, aliases or alternate spellings: equality is byte-exact up to the first NUL.

**Novel codes generated and entered.** There are none to generate: every literal the validator can accept is one of the ten ROM strings, and all ten appear verbatim in the published 3rd party cheat index list. A deliberately constructed *unpublished* input cannot be accepted by construction. This is not an untested assumption:

1. **Static count** — the validator contains exactly ten `BL strcmp` instructions (addresses listed in §4), each loading one of the ten table pointers from its own literal pool (`0x08028580`…`0x080287C0`), followed by one shared failure branch. No loop, table walk, checksum or second comparison path exists.
2. **Table count** — the record run at `0x0805F0B8` is exactly `0x50` bytes = 10 × 8, bounded by unrelated u32 data at `0x0805F0B4` and `0x0805F108`. Both stub headers were scanned and contain no code strings.
3. **Dynamic count** — all ten table strings were injected at the live breakpoint and produced `Code Accepted!` plus the expected effect (screenshots `t_SH33P.png` … `t_B41S0KV.png` in `/tmp/spyroorange3/`; `montage_codes.png`). Four out-of-set strings — `SHEEPXX`, `SH33PX` (valid prefix + one extra glyph), `AAAAAAA`, `1234567` — all produced `Invalid Code!` (`t_SHEEPXX.png`, `t_SH33PX.png`, `t_AAAAAAA.png`, `t_1234567.png`).

**Bounds proved by rejection.**

* *Not in table* → `Invalid Code!` (4 cases above).
* *Prefix-plus-extra* (`SH33PX`) → `Invalid Code!`, proving there is no prefix/partial match and no truncation to 5 characters.
* *Maximum-length pressure*: a 10-character input (`SHEEPXXAAA`, 10 glyphs) was accepted by the entry buffer and submitted; it reaches the same failure path, confirming the buffer does not create a hidden long-code branch.
* *Once-only bound*: `V1S10NS` first use → `You have received 100 gems!`; second use without reloading → `Code Accepted! / Code can only be used once!` (`once_first.png`, `once_second.png`). The gate is the byte at `save_record + 0x1DE + 0` (helper `0x08014970`), set by `0x0801497C`; index 1 is the `T4P10C4` flag. Reloading the savestate clears both flags and the gems are granted again, proving the bound is save-record state, not a dead code path.
* *Cosmetic modes*: palette changes are visible in the result screenshots for `SP4RX` (orange), `P0RT4L` (purple), `G3MZ` (grey) — `t_SP4RX.png`, `t_P0RT4L.png`, `t_G3MZ.png`.

**Other hidden surfaces (bounded negatives).**

* `Prototype Build` (`0x080D3094`) exists in the text bank but is absent from the rendered mode menu; eight Down presses on that menu never reveal a fifth item and the selector stays in the four-item ring. Classed as a cut/dead string, not a reachable menu.
* The published "hold L+R at power-on starts a secret Crash Party game" was tested by holding L+R before and throughout mGBA launch; this PAL build always booted the normal Spyro Orange title (`bootlr3.png`). Unverified here — no in-game input path was found for it.
* Shin'en `Code: B.Wodok` strings (`0x0808B365` etc.) are the GAX audio-engine banner, not cheat content (guide §16.1).

## 7. Validation evidence

* **Observed (emulator)**: code-entry screen and its 31-glyph keyboard; L+R gate (`KEYINPUT` `0x03FF` idle → `0x00FF` held); all ten accepted effects and their exact on-screen messages; four rejections; the once-only second-use message; live palette changes.
* **Observed (RAM / GDB stub)**: entry buffer `0x0200FB24` changing from `----------` to entered glyphs; breakpoint at `PC=0x08028546` with `r1=0x0805F0B8` (`SH33P`) and `r0=0x03007D30`; injected strings accepted/rejected by the game's own `strcmp`.
* **Derived (disassembly)**: ten-`strcmp` validator, string table and stride, message ID mapping, once-only flag offsets, gem/card effect calls, shared failure path, dead `Prototype Build` string.
* **Inferred (not fully exercised)**: the four cosmetic modes are thought to revert on reset (published guide; no save write observed in their branches); card indices 80/52 were passed to the card routine but the resulting card artwork was not opened; the Crash Party boot combo remains unverified.
* **Web lead**: 3rd party cheat indexes dark52 guide §8 supplied the ten published codes and the L+R gate; every literal was verified against the ROM before use. Fetched pages were treated as data only.

## 8. Unknowns

* Whether any non-retail/prototype build exposes `Prototype Build` as a real menu entry — no such build was analysed.
* The exact save-record base address for the once-only flag (only the `+0x1DE + index` offset relative to the record was recovered).
* Whether the Crash Party boot combo requires a link cable, a different region, or different timing; not reproduced here.
* Card 80 / card 52 artwork and the long-term persistence of the four cosmetic modes were not played past the result screen.

## 9. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings`, `grep`, Python 3 (struct/re/Capstone 5.0.7), `arm-none-eabi-objdump -M force-thumb`, mGBA 0.10.5 under Xvfb `:319` with openbox, `xdotool`, `scrot`, ImageMagick `montage`, and a small GDB-Remote-Serial-Protocol client (`rsp.py`, `rspd.py`, `mg.py`, `entry.py`, `oracle.py`) held in `/tmp/spyroorange3/`. No GameShark/CodeBreaker/Action Replay codes were used; no ROM or copyrighted asset is redistributed here.
