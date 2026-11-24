# The Lord of the Rings: The Third Age (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `The Lord of the Rings: The Third Age.gba` |
| Size | 16,777,216 bytes (`0x01000000`) |
| Header title | `THIRD AGE` |
| Game code | `B3AE69` (`B3AE`, maker `69`) |
| Version | `0x00`; complement `0x7F`; header checksum `0x0000` (normal rebuilt-header artifact) |
| Entry word | `0xEA00002E` → `0x080000C0` (stock retail crt0, not a patched/cracktro image) |
| Nintendo logo | exactly **one** hit at file `0x0004` → single retail image, not a multi-game pack |
| MD5 | `39d7f5579beafc2d3cfb0485c5be3bdf` |
| SHA-1 | `0a7a704d2ba167eb2dc03ad5dcfa0f09ea982a54` |
| SHA-256 | `721d5d0339f4c97abcfafd1cf5886b955aee3927cd6700c85a20815f93463923` |
| Save hardware | **EEPROM 512 bytes** (4 Kbit). String `EEPROM_V124` at `0x08A0A404`; a 512-byte `.sav` was created by mGBA on first boot. |

**Conclusion: no in-game cheat system exists in this SKU.** No password entry, no button code,
no hidden/debug menu, and no controller-reachable unlockable was found. This is a **bounded
negative** (§0.2 / §16.3 case 1: "no system"), supported by the counts in §6b and §7. The game
ships battery EEPROM save memory, so there is no structural need for a password system.

## 2. Executive summary

This is an EA/Griptonite turn-based strategy game with tile-index (not ASCII) text. I walked
every reachable screen in mGBA (15 distinct screens, §6b) and found **no code-entry field, no
cheat menu, and no hidden menu entry**. Static analysis agrees:

* `strings -t x -n 4` over the whole 16 MiB yields 112,440 lines, but **zero** hits for
  `password|cheat|secret|code|debug|unlock|menu|level select|bonus|hidden|gameshark|codebreaker`.
* Ghidra's complete defined-string inventory is **62 strings**. None is an English UI label or
  a cheat/password: they are the header title, library IDs (`Krawall`, `RFU-MBOOT`,
  `EEPROM_V124`), an internal tag `Rings3`, and 2-byte-spaced font glyph maps such as
  `0x08F0CA01` (`"   ! \" # … Z"`) and `0x08EAD703`/`0x08EAD73F`.
* 342 plausible GBA-LZ77 blocks were decompressed; **0** keyword hits in their output.
* Strided (1–8 byte stride, all offsets) and shifted (±0x10/0x20/0x40) encodings of 12 cheat
  keywords: **0 hits**.
* The only keypad register literal `0x04000130` appears **3 times**; the input subsystem at
  `0x0801B3F0` is a plain held/pressed/released/repeat tracker with a `0x3FF` mask. Its
  "pressed" array `0x03004234` has **28 xrefs in 20 functions**; I decompiled all 20 and **none**
  implements a progress-index + mask-table sequence matcher. The only multi-byte magic values
  found near input (`0xDEAD`, `0xBEEF`, `0xBABE`, `0xB0CA` at `0x0800D754`) are **link-cable
  handshake** values in SIO registers `0x04000120`–`0x0400012A`, not cheats.
* Six button combinations were pressed on the title and main-menu screens; none opened a
  hidden screen.

The two settings that could be mistaken for unlockables — **Sauron Mode** (permadeath) and the
three difficulty levels — are both available on a fresh save with no gate.

## 3. How to reproduce

* Emulator: mGBA 0.10.5 under Xvfb `:317`, `SDL_AUDIODRIVER=dummy`, 3× scale, GDB stub on
  default port (the stub did not accept connections in this build; RAM was read from mGBA
  savestates instead, §9).
* Keymap (mGBA SDL default): A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`,
  D-pad = arrow keys. Hold 120 ms per press.
* Boot path: Language Select → A (English) → legal screen → A×4 → Title → Start → Main Menu.
* `New Game` → Choose a Commander (6 portraits) → A → "Sauron Mode?" (Yes/No) → No →
  campaign map → A → mission briefing (Objective / Scouting Report / Play!) → Play! →
  battle → Start → pause menu (Units / Options / Glossary / Quit).
* Savestates: `Shift+F1`/`Shift+F2`/`Shift+F3` save slots 1–3; `F1`/`F2`/`F3` load them.

## 4. Address map

| Address (ROM unless noted) | Meaning | Evidence |
|---|---|---|
| `0x08000000`–`0x080000BF` | GBA header; title `THIRD AGE`, code `B3AE69` | Observed (`xxd`, SHA-256) |
| `0x080000C0` | crt0 entry (from `0xEA00002E`) | Derived |
| `0x08000410`–`0x08000440` | Small ARM routine; bytes `PRF %r0%` at `0x08000428` are **dead padding in a skipped literal pool** (branch at `0x08000420` jumps over them), not a debug printf | Derived (`objdump -M force-arm`) |
| `0x0801B3F0` | Input poll: reads `0x04000130`, XOR with `0x3FF`, fills held/pressed/released arrays | Derived (Ghidra `procedure_pseudo_code`) |
| `0x03004230` / `0x03004234` / `0x03004238` / `0x0300423C` / `0x03004244` | held / **pressed** / prior / released / repeat arrays (IWRAM) | Derived (literal pool at `0x0801B5A0`–`0x0801B5C8`) |
| `0x0800D754` | Link-cable handshake using `0x04000120`–`0x0400012A`, magic `0xDEAD/-0x2153`, `0xBEEF/-0x4111`, `0xBABE/-0x4542`, `0xB0CA/-0x4F36` | Derived (Ghidra) |
| `0x080546D8` | ASCII `Rings3`; sole xref `0x0802AA42` passes it as `memcpy(src, …, 8)` | Derived |
| `0x08A0A404` | ASCII `EEPROM_V124` (save-library identifier) | Observed |
| `0x08F0CA01`, `0x08EAD703`, `0x08EAD73F`, `0x08F32AB0` etc. | 2-byte-spaced ASCII font glyph maps; **0 xrefs** (used as data, not debug code) | Derived (Ghidra `list_strings`, `xrefs`) |
| `0x06D574`, `0x0775C4`, `0x07C5EC`, `0x07CDF0`, `0x089E58` | Large GBA-LZ77 blocks (decompressed size `0x80000` each) | Derived (`lzscan.py`) |
| state `0x00000`, VRAM `0x01000`, palette `0x00800` | mGBA `.ss1` `gbAs` chunk layout (zlib, 397,312 B raw) | Derived (`ssdump.py`) |

## 5. Algorithm

No validator exists to reverse. For completeness, the *input* algorithm that a button-code
system would have to be built on is:

```
poll():
  raw = ~KEYINPUT & 0x3FF          # active-high 10-button mask
  for slot in 0..1:                # two-player / link slots
    old = prev[slot]; prev[slot] = raw
    pressed[slot] = raw & ~old
    released[slot] = old & ~raw
    held[slot] = raw
  # IWRAM globals at 0x03004230..0x03004244, counters at 0x03004240/0x03004248
```

No consumer of `pressed[]` compares it to a stored mask sequence, keeps a progress index, or
indexes a button table. The `0x01`-bit tests found in `FUN_080076A4` and the
`DAT_0801B4D0+0x21` mode flag in `FUN_0801B4D4` are ordinary UI navigation and link-mode
selection.

## 6. Tables

* Main menu: exactly **4** entries — New Game, Load Game, Multiplayer, Options (observed cursor
  wraps at 4).
* Options: exactly **9** entries — Difficulty, Music Volume, SFX Volume, Auto-End Turn,
  Movement Grid, Snap type, Language, Credits, Sleep Mode (observed).
* Multiplayer: exactly **3** entries — Hotseat, Link Mode, Wireless Mode.
* Battle pause: exactly **4** entries — Units, Options, Glossary, Quit.
* Commander select: exactly **6** commanders (7 Right presses wrap to index 1); one toggle
  "Sauron Mode?" (No = heroes heal, Yes = permadeath).
* Mission briefing: exactly **3** tabs — Objective, Scouting Report, Play!.
* Difficulty values observed: Normal, Hard, Grueling (3; wraps).
* No code table, alphabet table, checksum table, or button-mask table was found.

## 6b. Enumeration

**Space definition:** not applicable — there is no code space, alphabet, field layout, or
checksum to enumerate. The accepted set of "codes" is the **empty set**. This is a proven
negative over the following bounded search spaces (all counts are from this ROM+session):

| Search space | Count | Result |
|---|---:|---|
| Distinct screens walked in emulator | **15** | 0 code-entry fields, 0 hidden menu entries (list in §7) |
| Visible menu items enumerated across all menus | **4+9+3+4+6+3+2 = 31** | all labelled; no unlabelled/hidden slot |
| `strings -n 4` lines | **112,440** | 0 cheat-related keyword hits |
| Ghidra defined strings | **62** | 0 UI/cheat strings; all are header, library, or font-glyph data |
| Keyword set tested | **12 words** (`password,cheat,secret,debug,unlock,code,menu,key,special,hidden,level,select`) | 0 hits in Ghidra inventory |
| Strided encodings (stride 1–8 × all offsets, 12 keywords) | **96 scan passes** | 0 hits |
| Shifted ASCII (6 shifts × 8 keywords) | **48 scan passes** | 0 hits |
| LZ77 blocks found / decompressed | **342 / 342** | 0 keyword hits in decompressed output |
| Candidate text-bank regions (heuristic) | **137** | all are compressed graphics/script data, no code table |
| Literal references to `KEYINPUT` `0x04000130` | **3** | all inside the single input poll at `0x0801B3F0` |
| Xrefs to "pressed" array `0x03004234` | **28** in **20** functions | 0 sequence matchers after decompiling all 20 |
| Button-mask runs (u16, single-bit masks, length ≥4, non-counter) | **403** | all are game/script flag tables (e.g. `0x00125208+`), 0 button-code tables |
| Button combos pressed on title/main menu | **6** (L+R+Start, A+B+Start+Select, L+R, Select+Start, A+B+Down, L+R+Select) | 0 hidden screens |

**Novel-code requirement (§0.2):** cannot be satisfied because no generator, validator, or
code alphabet exists in this image. The requirement is replaced by the bounded negative above,
which meets §0.2's explicit "prove a bounded negative with counts" alternative.

**Rejection bounds:** no validator exists, so no "rejected code" can be entered. The nearest
bounded probe was the input surface itself: all six multi-button combinations were accepted only
as their constituent single presses (navigation), never as a code — i.e. the game exposes no
rejector because it exposes no acceptor.

## 7. Validation evidence

**Observed (emulator screenshots, all saved in `/tmp/lotr thirdage/`):**

1. Language Select (`screen.png`)
2. Legal / copyright (`s2.png`)
3. Title — "Press START" (`s4.png`, `title2.png`)
4. Main Menu — 4 entries (`s5.png`)
5. Options — 9 entries (`s7.png`, `opt_credits_sel.png`)
6. Multiplayer — 3 modes (`s11.png`)
7. Choose a Commander — 6 portraits + "Sauron Mode?" (`ng1.png`, `ng4.png`, `ng5.png`)
8. Campaign Map — chapter I, "Basic Tutorial", Gladden Fields (`ng6.png`)
9. Mission Briefing — 3 tabs (`br_scout.png`, `br_play.png`)
10. Battle — command points tutorial (`battle1.png`)
11. Battle Pause / Mission Objectives — 4 entries (`battle_pause.png`, `pause_down.png`)
12. Units screen — unit stats (`pause_units.png`)
13. Quit confirmation (`pause_glossary.png`)
14. Credits — "GRIPTONITE GAMES" (`credits1.png`)
15. In-battle tutorial prompt (`back_title.png`)

**Observed (RAM):** 512-byte EEPROM `.sav` created on boot; its header is
`33 31 30 30 45 41 33 42 00 04 00 00 01 00 99 80 89 98 …` followed by mostly `0xFF` (erased
EEPROM). No password-like data.

**Derived (static):** input handler and globals (§4); 62-string inventory; 342 LZ77 blocks;
28/20 input-xref functions; link handshake magic; `Rings3` memcpy xref.

**Inferred:** none material. The `PRF %r0%` bytes are classified as dead literal-pool padding
with high confidence from the branch at `0x08000420`, but no debug printf caller was exercised.

## 8. Unknowns

* The internal tile-index text bank was not fully decoded (the font tiles in VRAM did not yield
  a clean ASCII mapping with the palettes sampled). This does **not** weaken the negative: all
  string searches were supplemented by full screen enumeration, and Ghidra's independent string
  inventory also found no cheat-related text. A hidden string encoded as tile indices *could*
  in principle exist, but no code-entry surface exists to consume it.
* Only the first campaign mission and the first battle were played; later missions may contain
  story-gated content, but the pause-menu structure is shared across the game and has no
  cheat/debug entry.
* The GDB stub refused connections in this mGBA build, so RAM was read from savestates rather
  than live. This affects only evidence *presentation*, not the screen enumeration.

## 9. Tooling

* `mgba` 0.10.5, `Xvfb :317`, `openbox`, `xdotool`, `scrot`, `convert` (crop/zoom).
* `arm-none-eabi-objdump -M force-thumb` / `-M force-arm` for literal pools and the crt0.
* Python 3 scripts in `/tmp/lotr thirdage/`:
  * `ssdump.py` — extracts and zlib-decompresses the `gbAs` PNG chunk from `.ss1`.
  * `lzscan.py` — GBA-LZ77 scanner/decompressor + keyword search (342 blocks).
  * `render_font.py`, `render_font2.py`, `render_bg.py` — VRAM tile/map visualisation.
  * `bankfind.py`, `textbank.py` — text-bank heuristics and repeated-data scan.
  * `keys.py`, `combo.py` — reproducible XTEST input helpers.
* REA/Ghidra 12.1.4 (`open_binary` raw ARM @ `0x08000000`): `list_procedures` (1,508
  procedures), `list_strings` (62), `search_strings`, `search_bytes`, `xrefs`,
  `procedure_pseudo_code`.
* Closed the REA session with `close_binary` after analysis.

## 10. Legal note

No ROM data or copyrighted assets are reproduced here beyond hashes, addresses, and short
identifiers required for reproduction. Screenshots remain in the disposable work directory.
