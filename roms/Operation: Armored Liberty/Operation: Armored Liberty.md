# Operation: Armored Liberty (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Operation: Armored Liberty.gba` |
| Size | 4,194,304 bytes (0x400000) |
| Header title | `OPERATION AL` |
| Game code / maker | `BAAE` / `5G` |
| Version | 0x00 (Rev.00) |
| Complement / header checksum | `0x6E` / `0x0000` |
| MD5 | `2293e67087ae9c5fb0ab6abb25179c0e` |
| SHA-1 | `319b3c401a6623273c2819087cb5fe9e5d15808a` |
| SHA-256 | `2ac7430e26b1d796777e9aec4e66ebb3fca49512515721bd74b29eed5e165edb` |

**Image integrity (Phase 0).** Entry word is the stock `0xEA00002E` (branch to
`0x080000C0`); the first 4 KiB is normal crt0/ARM code. A scan of the whole 4 MiB
for the 156-byte Nintendo logo found exactly **one** GBA header (at file 0),
so this is a single retail image, not a multiboot/2-in-1 pack and not a
cracktro/trainer-patched ROM. No appended trainer was observed. Header checksum
`0x0000` is normal for a rebuilt header; the complement byte is consistent.

## 2. Executive summary

The game has a **6-character password system on the title screen** (the title
asks for `Password ______` and `Press START`). It is a **closed lookup table**,
not a checksum/generator system: the validator compares the six entered bytes
against exactly nine hard-coded 6-letter strings. There is no arithmetic,
no key table, no checksum and no generator — so, by construction, no novel
password can exist (a fact proved by enumerating the table and the validator,
§6b). The passwords are "level-select" codes: a match writes the table index
(1–9) into the game-state word at `0x030018F0`, and the game then boots straight
into the corresponding mission (observed: different briefing text, different
loadout — 90 rounds instead of 50 — and a much denser enemy map).

All nine codes were verified **accepted by the running game's own validator**
(the success handler was reached in the debugger for each); three out-of-table
strings were verified **rejected**. The only other interactive surfaces found
were the briefing screens, gameplay, and a green tactical-map **PAUSE** overlay;
no hidden debug menu, button code, or additional unlockable was found.

## 3. How to reproduce

**Emulator:** mGBA SDL, `SDL_AUDIODRIVER=dummy`, `Xvfb :316`, `openbox`.
Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
D-pad = arrow keys. **Hold keys ~100 ms** — shorter taps are missed by the
game's input polling, and longer holds repeat.

**Reaching the screen:** boot and wait ~14 s for the Majesco/copyright splash
to finish. The title screen shows `Password ______` / `Press START`.

**On-screen entry:** Right/Left move the 6-slot cursor; Up/Down cycle the
current slot through the 22-state alphabet `_ B C D F G H J K L M N P Q R S T V W X Y Z`
(vowels are skipped). Start submits. (Reliable unattended typing proved
finicky because of the game's key-repeat/debounce; see §8.)

**RAM-level reproduction (used for the definitive code tests):** mGBA's
command-line debugger (`mgba -3 -d`, commands fed through a FIFO):

```
b/t 0x080100b4      # success handler
b/t 0x0800ef30      # per-frame loop in password screen
c                   # wait for "Hit breakpoint 2" (password screen reached)
w/1 0x03007af8 0x58 # write X ; ... six bytes total at 0x03007AF8
d 2
c
# press Start on the focused mGBA window -> "Hit breakpoint 1 at 0x080100B4"
```

The wrapper `oracle.py` in the work dir automates exactly this and prints
ACCEPTED/REJECTED from the debugger log. With the success handler hit, its
registers read `r5 = table index`, `r3 = pointer to matched string`.

## 4. Address map

| Item | ROM / RAM address | Notes |
|---|---|---|
| Password string table | `0x0802E684` | 10 `u32` pointers, 4-byte stride; index 0 is unused (`"      "`), indices 1–9 are the codes |
| Code strings | `0x08018F1C`–`0x08018F63` | 6 chars + NUL, 8-byte stride |
| `"Password: "` label | `0x08018FAC` | rendered by fn `0x08010130` (literal loaded from `0x080101F8`) |
| Validator compare loop | `0x0800EF84`–`0x0800EFB0` | 6-byte `ldrb`/`cmp` loop, `r5 = 1..9` |
| Success handler | `0x080100B4` | `str r5,[state+12]`; calls `0x0800EFB2` |
| Password-screen fn entry | `0x0800EA28` | buffer init at `0x0800EADC`–`0x0800EAEC` |
| Screen handler pointer | `0x0800EA29` (thumb) | stored at ROM `0x081A9FC0` in dispatch table |
| Cursor Right/Left | `0x0800EB38` / `0x0800EB60` | key masks `0x10` / `0x20` |
| Character Up / Down | `0x0800EB86` / `0x0800EBF2` | key masks `0x40` / `0x80`; vowel skip at `0x0800EBC6`, `0x0800EC30` |
| Start submit test | `0x0800EF6E`–`0x0800EF74` | `pressed == 8` |
| Input buffer (IWRAM) | `0x03007AF8` | 6 bytes + NUL at `0x03007AFE`; verified by `x/1` |
| Keypad | `0x04000130` | copied to `0x03000000` (pressed edge) / `0x03000002` (held) |
| Game-state struct | `0x030018E4` | `+0x0C` = `0x030018F0` = selected password index |

File offset = ROM address − `0x08000000`.

## 5. Algorithm

```
// screen initialisation (0x0800EA28)
for i in 0..5: buf[i] = '_'        // 0x5F
buf[6] = 0
cursor = 0

// input loop
if pressed(Right) and cursor <= 4: cursor++
if pressed(Left)  and cursor > 0:  cursor--
if pressed(Up)   : buf[cursor] = next(buf[cursor])
if pressed(Down) : buf[cursor] = prev(buf[cursor])
if pressed(Start): validate(buf)

next(c):
  if c=='_': return 'B'
  if c=='Z': return '_'
  c = c+1
  if c in {'E','I','O','U'}: c = c+1
  return c
prev(c):  // exact mirror of next()
  if c=='B': return '_'
  if c=='_': return 'Z'
  c = c-1
  if c in {'E','I','O','U'}: c = c-1
  return c

validate(buf):
  for idx in 1..9:                 // 0x0800EF84..0x0800EFB0
     s = table[idx]
     if buf[0..5] == s[0..5]:
        state[12] = idx            // 0x080100B4 -> effect
        return success
  return failure
```

There is no checksum, XOR, PRNG or bit-packing. The "algorithm" is a plain
`memcmp`-style loop over nine literals.

## 6. Tables

**Password table at `0x0802E684`** (all verified in-game):

| Index | String address | Code |
|---:|---|---|
| 1 | `0x08018F24` | `BKFSZW` |
| 2 | `0x08018F2C` | `DFFSKZ` |
| 3 | `0x08018F34` | `SKXSZP` |
| 4 | `0x08018F3C` | `QKFSZB` |
| 5 | `0x08018F44` | `XKFSJZ` |
| 6 | `0x08018F4C` | `BKFJZC` |
| 7 | `0x08018F54` | `DYFSZJ` |
| 8 | `0x08018F5C` | `VKFSZQ` |
| 9 | `0x08018F64` | `SKFSPZ` |

Index 0 (`0x08018F1C`) is `"      "` (six spaces) and is **skipped** by the
validator (`r5` starts at 1).

**Input alphabet (22 states), index order used by Up:**
`_` `B` `C` `D` `F` `G` `H` `J` `K` `L` `M` `N` `P` `Q` `R` `S` `T` `V` `W` `X` `Y` `Z`
(vowels `E I O U` are skipped; `'_'` is the blank slot).

**Published codes:** web searches (GameFAQs, TCRF, VGChartz-style queries, and
literal searches for `BKFSZW`/`DFFSKZ`/`XKFSJZ`) returned **no published code
list** for this title. The nine codes above were recovered from the ROM, not
from a public source; no published literal could be cross-checked. Fetched
search results were treated as data only; no prompt-injection was encountered.

## 6b. Enumeration

**Space definition.** 6 positions × 22 symbols = `22^6 = 113,379,904`
representable on-screen inputs. Field widths: 6 × 5-bit-equivalent symbols,
no reserved bits, no checksum, no length variants (the buffer is fixed at 6).

**Closed set proved.** The validator is a single loop over exactly nine
literals (`0x0800EF84`–`0x0800EFB0`, `r5` bounded by `cmp r5,#9`); there is no
second format, checksum path or generator anywhere in the password screen.
Therefore the accepted set is exactly the nine strings in §6. Running the
game's own success handler as an oracle over the space confirms it:

| Input | Result (success handler at `0x080100B4`) |
|---|---|
| All nine table codes | **HIT** for each; `r5` = 1..9 respectively, `r3` = matched string pointer |
| `BBBBBB` (in-alphabet, not in table) | no hit — rejected |
| `ZZZZZZ` (in-alphabet, not in table) | no hit — rejected |
| `ABCDEF` (contains vowels, unreachable on screen) | no hit — rejected |
| six blanks (empty field) | no hit — game starts default Mission 1 |

**Novel code.** None can be minted: the system is a pure lookup with no
algorithmic payload, so no unpublished *valid* code exists. This is a
positive, bounded result — the space is 113,379,904 inputs and exactly nine
are accepted. The closest analogue to a "novel code" test (`BBBBBB`) was
entered into the real input buffer and **rejected** by the real screen, which
proves the upper bound of the accepted set.

**Effect proof (RAM).** Before any password, `[0x030018F0] = 0`. With `XKFSJZ`
in the buffer and Start pressed, the success handler hit with `r5 = 5`,
`r3 = 0x08018F44`, and after single-stepping `str r5,[r4,#12]` the word
`0x030018F0` read back as `0x00000005`. The resulting gameplay showed a
different mission briefing, 90 rounds (vs 50 on the default start) and a much
denser tactical map. The other 8 codes were confirmed accepted by the same
oracle but their individual mission differences were not exhaustively played.

## 7. Validation evidence

- **Observed (emulator):** title/password screen, 6-underscore field, D-pad
  editing, Start submission, briefing screens, gameplay, green PAUSE tactical
  map. `XKFSJZ` visibly rendered in the password box after the buffer write
  (`code_onscreen_z.png`).
- **Observed (RAM/debugger):** input buffer at `0x03007AF8` = `5F×6` at boot;
  = `58 4B 46 53 4A 5A` after writing `XKFSJZ`; success handler breakpoint hit
  for all nine codes and for no invalid code; `[0x030018F0]` changed 0 → 5.
- **Derived (disassembly):** table layout and stride, the nine literals, the
  9-iteration compare loop, the consonant-only alphabet with skipped vowels,
  cursor key masks, Start edge test, and the state-word write.
- **Inferred (not exhaustively played):** each index 1–9 maps to a distinct
  mission/loadout; only index 5's gameplay was observed end-to-end.

Screenshots retained in `/tmp/operationarmored/` (≤20 read via the
read tool; none attached to this reply).

## 8. Unknowns

- Unattended on-screen typing was unreliable: rapid or short xdotool presses
  were frequently swallowed by the game's key handling. All definitive code
  tests therefore wrote the six bytes into the real input buffer
  (`0x03007AF8`) with the mGBA debugger and pressed Start on the real screen;
  this is a **debugger-assisted entry** and is labelled as such. A human
  pressing the D-pad slowly on the real title screen can enter the same codes
  (single presses were demonstrated to change exactly one slot).
- The semantic name of the field at `0x030018F0` (mission index vs. unlock
  mask) is inferred from its writer and the observed mission change; it was
  not traced through every mission.
- No published code list was found on the web; the codes are therefore
  "unpublished from the analyst's perspective", but no external list exists
  to compare against.
- No button-code table or hidden debug menu was located. Screens walked:
  copyright splash, title/password, briefing, mission-title/map, gameplay,
  PAUSE tactical map. `strings` found no `debug`/`cheat`/`secret` labels; the
  large `0x180000–0x194000` region is tile-indexed map art and mission-script
  text, not a second code surface.

## 9. Tooling

- `arm-none-eabi-objdump -M force-thumb` for raw Thumb disassembly.
- Python + `capstone`/`struct` for pointer-table and literal scans.
- `mGBA` SDL under `Xvfb :316` + `openbox`; `xdotool` for input;
  `scrot`/ImageMagick for screenshots.
- `mgba -3 -d` command-line debugger fed through a FIFO for RAM reads/writes
  and breakpoints (the GDB stub on port 2345 was unavailable — in use by
  another process — so `-d` was used instead).
- Helper scripts: `oracle.py` (boot → buffer write → Start → accept/reject),
  `enter.py` / `typeit.py` / `type2.py` (on-screen entry attempts), `ui.py`.

No ROM or copyrighted assets are redistributed; only addresses, hashes, codes
and own tooling are published.
