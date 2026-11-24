# Rescue Heroes: Billy Blazes (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `Rescue Heroes: Billy Blazes.gba` |
| Size | 4,194,304 bytes (0x400000, 4 MiB) |
| Header title | `BILLY BLAZES` |
| Game code | `AQHE` (USA) |
| Maker code | `7D` |
| Version | 0x00 (Rev.00) |
| Entry word | `0xEA00002E` (stock GBA `b 0x080000C0`) |
| Fixed 0x96 | present (`rom[0xB2] == 0x96`) |
| MD5 | `7d1a892dc265ce90f16aec38e366afcd` |
| SHA-1 | `9d61dc07e62deca5f51f7569e12517dbc78a9b5b` |
| SHA-256 | `d9be26a2dbbc1aad619e9567a520637667cbbbc6cc4d6e165fbdfe5dc4910a17` |

**Phase 0 / §16.1:** A full-file scan for the 156-byte Nintendo logo finds exactly one
GBA header, at file offset 0. The header checksum word is `0x0000` with complement byte
`0x5A`, and the entry word is the stock `0xEA00002E`, so the header itself was not
rebuilt for a trainer. However the *boot sequence* starts with a scene-release cracktro
(a text screen crediting AGGRESSION / ANTHROX / DOS ILLUSION / SNEAKERS / SWAT /
EURASIA / VENOM / MENACE / LIGHTFORCE / RISING / "the new school legacy"), which
auto-advances to the genuine WayForward logo and then the title screen. It exposes no
menu of its own and is a release splash, not an in-game cheat. No GameShark /
CodeBreaker trainer functionality was found; `*.sav` produced by mGBA is 0 bytes (the
game has no usable battery save and uses its Password screen instead).

## 2. Executive summary

The game has a genuine in-game **Password** screen on the main Mode Select menu. It is
a 4-slot keypad arranged as a 2×2 grid. D-pad moves a clamped cursor between the four
cells; A increments and B decrements the shape in the selected cell. Six shape values
exist: 0 = blank blue square, 1 = white circle, 2 = red triangle, 3 = yellow cross,
4 = black dash, 5 = green X. Start submits.

The four values are stored in IWRAM as little-endian u16 at `0x03004188 + 0x58*i`
(i = 0..3), each duplicated at `+2`. This was proved by a savestate diff after entering
a distinctive 1/2/4/3 pattern and by a live GDB read. Patch those four words in an mGBA
`.ss1` (zlib `gbAs` chunk) to submit an arbitrary code without replaying the UI.

**Enumeration result (§0.2):** the full usable space is 5^4 = 625 codes for symbols
1–5 (6^4 = 1296 including the blank symbol 0). All 625 non-blank codes were submitted
to the real screen, one by one, using the savestate oracle; **zero were accepted**.
Blank-containing codes take the same rejection path (sample tested, including all-zero
and `0 1 2 3` / `1 0 2 3` / `1 2 0 3` / `1 2 3 0`). Rejection is unambiguous: the
screen darkens, the tile-indexed message **"Incorrect password!"** is drawn, then the
slots reset to blank and/or the game returns to the title screen. Because every input
in the space is rejected, no novel accepted code can be minted — this is a *proven
negative*, not an untested one (§0.2 clause 5).

A developer debug menu is present as data: a 0x20-stride ASCII label table at
`0x0801E04C` with 86 entries including `GET PASSWORD`, `SET PASSWORD`, `SOUND TEST`,
`TRAINING1..4`, `W3TEWEST`, `SONG 0..16` and all scene names. `SET PASSWORD` is the most
plausible explanation for the all-reject result (the expected code is supplied by that
debug path, which shipped controls cannot reach) — see §8.

## 3. How to reproduce

Emulator: mGBA SDL build under `Xvfb :316`, `SDL_AUDIODRIVER=dummy`, `-3` scale.
Keymap: A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`,
D-pad = arrow keys. Hold keys 60–80 ms; 150 ms double-steps the cursor (§16.2).

Menu path: boot → title → Start → Mode Select (`New Game`, `Training Mode`,
`Password`) → Down, Down → Password. On the Password screen, D-pad selects a cell,
A/B cycle the shape, Start submits.

To reproduce the exhaustive test:
1. Boot to the Password screen (`press Start, Down, Down, A`) and save state slot 1
   (`Shift+F1`).
2. For each code `(a,b,c,d)`, write the four u16 values into the state's `gbAs` chunk
   at PNG-file offsets `0x1D188 + 0x58*i` and `0x1D18A + 0x58*i`, rebuild the PNG with
   correct CRCs, press `F1` to load, then `Return` to submit.
3. Wait 3.45 s and classify: match against the title-screen reference → reject; match
   against the cleared-password reference → reject; anything else → accept. A second
   sample at +1.2 s disambiguates slow transitions. (Both references are stable at
   4.0 s; a 5-code control set classified correctly.)
4. The sweep script is `brute_good.py` in the work dir; its log `brute_good.log`
   records `progress 0/50/.../600` and ends `DONE 0`.

All screenshots were taken with `scrot` and cropped from the 720×480 viewport at
screen offset +152,+144.

## 4. Address map

| Item | Address / file offset | Evidence |
|---|---|---|
| Password slot i (u16) | IWRAM `0x03004188 + 0x58*i`, i=0..3 | Observed: savestate diff + GDB `x/4hx 0x03004188` |
| Password slot duplicate | IWRAM `0x0300418A + 0x58*i` | Observed: cycles with the slot |
| Cursor index | IWRAM `0x03002030` | Derived: savestate diff (0→1 on Right) |
| Debug label table | `0x0801E04C`, 0x20-stride, 86 entries | Derived: raw bytes + `strings -t x` |
| Credits label table | `0x0801F8AC`, 0x20-stride | Derived |
| Key-input register | `0x04000130` | Derived: literal pointer at `0x0800CE74` |
| Password screen handler | `0x08018384` (Thumb) | Observed: return address on live stack; REA/Ghidra dossier |
| Scene-handler pointer | `0x0801DBF4` → `0x08018385` | Derived: literal scan and Ghidra xref at `0x080002F0` |
| mGBA state IWRAM base | file offset `0x19000` ↔ `0x03000000` | Derived: GDB/savestate cross-check |
| mGBA state VRAM base | file offset `0x10000` | Derived: savestate layout |

File offset = ROM address − `0x08000000` throughout.

## 5. Algorithm

Reconstructed input/validation model:

```
slot[4]                      # u16 at 0x03004188 + 0x58*i
 alphabet = {0:blank, 1:circle, 2:triangle, 3:cross, 4:dash, 5:X}
 A: slot[cursor] = (slot[cursor] + 1) % 6
 B: slot[cursor] = (slot[cursor] - 1) % 6
 D-pad: cursor = clamped 2x2 grid move
 on Start:
   submit (slot[0], slot[1], slot[2], slot[3])
   accept  -> gameplay / level start                 (NEVER observed)
   reject  -> "Incorrect password!" tile text, then
              slots reset to 0 and/or return to title  (OBSERVED for all tested inputs)
```

The ROM's own accept routine could not be isolated because no input ever reaches an
accept branch; the validator function is therefore reported as unknown (§8) rather
than guessed. The `B` decrement wraps 0→5 and 5→0 (verified in RAM), so the alphabet
is a 6-cycle.

## 6. Tables

Shape alphabet (index → glyph, observed on screen):

| Index | Glyph |
|---:|---|
| 0 | blank blue square (no input) |
| 1 | white circle |
| 2 | red triangle |
| 3 | yellow cross / plus |
| 4 | black dash |
| 5 | green X |

Debug label table at `0x0801E04C + 0x20*n` (86 entries, NUL-padded), full list captured
in work dir `debug_labels.txt`. Notable entries:

| n | Label |
|---:|---|
| 5 | GET PASSWORD |
| 6 | SET PASSWORD |
| 37 | CREDITS |
| 38 | TUTORIAL |
| 39–42 | TRAINING1..4 |
| 43 | SOUND TEST |
| 63 | W3TEWEST |
| 66–82 | SONG 16 … SONG 0 |

## 6b. Enumeration

**Space definition.** Four symbols × six values = 6^4 = 1296 representable codes.
Value 0 is the blank square; codes that use it still trigger the same reject path
(test vectors `0 1 2 3`, `1 0 2 3`, `1 2 0 3`, `1 2 3 0`, `0 0 0 0` all end on the
password/title reject state). The "typed" alphabet is therefore effectively 1–5,
5^4 = 625 codes.

**Exhaustive check.** All 625 codes `[a,b,c,d]` with `a,b,c,d ∈ {1..5}` were submitted
through the real Password screen using the savestate oracle and a screenshot classifier
calibrated on five known rejects. Result: **0 accepted, 625 rejected**. No code from
any published list was available to cross-check (GameFAQs returned HTTP 403, Bing and
DuckDuckGo search results were unrelated/polluted, TCRF and the Wayback Machine returned
404 for this title), so there is no external list to be a "novel code" relative to.

**Novel code / bounds.** Because the accepted set is empty, no code can be minted that
the game accepts — §0.2's "generate a novel accepted code" deliverable is impossible for
this ROM and is replaced by the bounded negative. Bounds were proven by rejection:
every representable non-blank code produces the "Incorrect password!" rejection and a
reset/title, not silence or a crash. The rejection was recorded both visually
(`titleref_g.png` shows the tile-indexed "Incorrect password!" message) and by the
classifier endpoints (`title_ref.png`, `pwclear_ref.png`).

**Debug-menu alternative.** The ROM contains the label table for a scene/sound-test
debug menu with `GET PASSWORD` and `SET PASSWORD`, but no shipped-input entry route was
found (L+R, L+R+Start, Select+Start, A+B+Start, L+R+A+B, Up-Up-Down-Down and
Start+Select+A+B were tried on the title screen; L+R held through boot also failed).
Consequently the debug setter cannot be used to make the Password screen accept.

## 7. Validation evidence

- **Observed** — title screen, Mode Select (New Game / Training Mode / Password),
  Training Mode (Tutorial / Time Trial → 1 Player / 2 Players), Difficulty
  (Advanced / Rookie), gameplay, pause menu (Continue / Quit), Password screen,
  "Incorrect password!" reject message, RAM buffer values, full 625-code sweep.
- **Derived** — address map, alphabets, handler addresses from `objdump -M force-thumb`
  and REA/Ghidra decompilation of `0x08018384` and `0x080002F0`.
- **Inferred** — the `SET PASSWORD` debug entry supplying the expected code and the
  all-reject result being a gate/cut feature rather than a typo in the public list.
  This is not proven: the validator itself was never isolated because no input reaches
  an accept branch.

## 8. Unknowns

- The validator function and the location/format of the "correct" code it compares
  against. Given the all-reject sweep, the expected value is likely written only by the
  unreachable debug `SET PASSWORD` path (§16.3 gated-feature case), but a live breakpoint
  on an accept branch could not be set because no input reaches one.
- Debug-menu entry sequence from shipped controls (the label table is data with no
  direct ASCII xref; no button combo among those tried reached it).
- Meaning of the `W3TEWEST` debug label (index 63).
- The tile indices/font bank of the "Incorrect password!" message were observed as
  rendered pixels but not decoded to a ROM text table; no ASCII/UTF-16 copy of the
  string exists in the image, so the message is bitmap/tile-indexed.

## 9. Tooling

- `file`, `md5sum`, `sha1sum`, `sha256sum`, `xxd`, `strings -t x`, `grep -abo`.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb`.
- Python 3 + `capstone` for PC-relative literal/BL scans, Pillow for screenshot
  classification, `struct`/`zlib` for mGBA savestate (`gbAs` chunk) patching/diffing.
- mGBA SDL (`-3`, `-t`, `-g`, `-d`), Xvfb `:316`, openbox, xdotool, scrot, ImageMagick.
- REA/Ghidra raw-binary import at `0x08000000` (ARM) with dossiers on `0x08018384`
  (password screen handler), `0x080104C8`, `0x080002F0`, and xrefs on `0x0801DBF4`.
- Work dir: `/tmp/rescueheroes`; key artifacts: `phase0.py`, `ptrscan_fast.py`,
  `ldrscan.py`, `ssdiff.py`, `sspatch.py`, `bufref.py`, `brute_good.py`,
  `brute_good.log` (ends `DONE 0`), `debug_labels.txt`, `title_ref.png`,
  `pwclear_ref.png`, `titleref_g.png`.

## 10. Legal note

No ROM or copyrighted assets are redistributed. Only hashes, addresses, algorithms,
and original observations are published.
