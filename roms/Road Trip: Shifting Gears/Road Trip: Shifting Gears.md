# Road Trip: Shifting Gears (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Road Trip: Shifting Gears.gba` (4,194,304 bytes = 0x400000) |
| Header title | `ROADTRIPSHIF` (12-char field; full title "Road Trip: Shifting Gears") |
| Game code / maker | `A6RE` / `5Z` |
| Version | 0x00 |
| Entry word | `0xEA00002E` — stock GBA branch to 0x080000C0 (no cracktro patch) |
| Header check | checksum @0xBE = 0x0000; complement @0xBD = 0x25, recomputed expected 0x3E → header was edited/rebuilt (common for a region/title rename); no appended trainer |
| Embedded headers | 1 (Nintendo logo scan) → single 4 MiB image, no multiboot/double-pack |
| MD5 | `740f84915f53447d3afb111acdfb0677` |
| SHA-1 | `9a332cec82dff9130248a2525d0151fae52dd258` |
| SHA-256 | `fe8256ea951832bf1518c8d2139921447d0f6b9413b95909e306a789108b5642` |
| Build tag | `TAKARA2002CHORO-Q201` at 0x3F5528, followed by a Thumb function-pointer table at 0x3F5540 |

This is the US release of Takara's *Choro Q Advance 2* (JP) / *Gadget Racers* (EU), developed by Electronics Application.

## 2. Executive summary

The game has **one** developer-intended cheat: the six-letter driver-name password **`DRAGON`**, entered at Options → Change Name, which unlocks the Dragon-series parts (GameFAQs "Passwords" entry). The code is real and present in the ROM — but **not as ASCII**: all in-game text is stored as one-byte font/tile indices, so `strings` finds only the link-debug printf bank at 0x29812C, never the password or any menu label.

`DRAGON` is stored as the 7-byte font-index field `0F 1D 0C 12 1A 19 0A` (plus `0x5F` terminator) at ROM `0x083EF898`, inside the system-menu pointer table at `0x083EF8A0`. The validator at `0x08013D04` compares the 7-byte saved driver-name field against that single literal, byte for byte. On success it calls a mark-unlock helper eight times, granting the completion marks that gate the Dragon (Devil/Angel-tier equivalent) parts. There is no checksum, no PRNG, no key table and no second algorithmic password format: the accepted space is exactly one string. I typed `DRAGON` on the real Name Entry screen and RAM-verified both the on-screen input buffer (`0x03002E88`) and its copy in the save structure (`0x02000F28`); an invalid name (`AAAAAA`) fails at the very first byte comparison.

No button-code table, hidden debug menu, or additional published code was found for this SKU. The only debug-related strings are GameCube-link logging strings (`INITAIL CODE`, `FROM HOST`, `CHANNEL`, `HOST ID`, `SESSION ID`, `OPEN`, `CLOSE`) at 0x29812C-0x2981D1 — a printf bank, not a player-facing cheat screen.

## 3. How to reproduce

1. Emulator: mGBA (SDL), `SDL_AUDIODRIVER=dummy`, `Xvfb :315 -screen 0 1024x768x24`, `DISPLAY=:315`; `mgba -3 <rom>` (or `-g` for the GDB stub, default port 2345).
2. Keymap used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad = arrow keys. Hold 100 ms, gap 220 ms; the on-screen keyboard drops very short taps.
3. Boot: NOTE screen → A; title → Start; menu `New Game` / `Quick Play` → A on `New Game` → **Name Entry**.
4. On-screen keyboard grid (cursor begins at `A`): row 1 `ABCDE FGHIJ KLMNO`, row 2 `PQRST UVWXY Z`. Move with D-pad, press A to insert, B to backspace, Start jumps to `End`, Select jumps to `Back`.
5. To type `DRAGON` from the initial cursor: `Right×3 + A` (D), `Down + Left + A` (R), `Up + Left×2 + A` (A), `Right×6 + A` (G), `Right×8 + A` (O), `Left + A` (N). The 7th slot stays blank (`0x0A`). Press Start then A to confirm.
6. Verification by RAM (mGBA GDB stub):
   - `x/8bx 0x03002E88` → `0f 1d 0c 12 1a 19 0a 5f`
   - after confirming, `x/8bx 0x02000F28` → `0f 1d 0c 12 1a 19 0a 5f`
7. Rejection test: type `AAAAAA` (six A presses) and confirm; `0x03002E88` becomes `0c 0c 0c 0c 0c 0a 0a 5f`, which fails the first `cmp r0, r3` at 0x08013D18 (expected 0x0F).
8. Published code verified: GameFAQs (archived) "Unlock Dragon Parts — enter DRAGON as your name", at `web.archive.org/web/20181126/https://gamefaqs.gamespot.com/gba/915135-road-trip-shifting-gears/cheats`. Cheat Happens lists no codes for this SKU; the GameFAQs list contains exactly one password and one progress-based unlockable (Super Cups).

## 4. Address map

All ROM addresses are `0x08000000 + file offset` (the image is not mirrored/split).

| Address | Kind | Meaning |
|---|---|---|
| 0x08000000 | code | Stock ARM entry branch `0xEA00002E` |
| 0x08013D04–0x08013D34 | code | **Password validator** (inside screen handler 0x080139F0, dispatch case 6) |
| 0x08013D36–0x08013DD4 | code | Unlock path: eight calls to 0x080189F0 |
| 0x080189F0 | code | Mark-set helper: `OR 0x05` into the byte at `markBase[slot] + offset` |
| 0x080188CC | code | `return *(u32*)(0x083EFCB0 + 4*slot) + offset` |
| 0x083EF870 | data | Encoded string `Change name?` |
| 0x083EF87D | data | Encoded string `Clear data?` |
| 0x083EF889 | data | Encoded string `Back to title?` |
| **0x083EF898** | data | **Encoded password `DRAGON `** — `0F 1D 0C 12 1A 19 0A 5F` |
| 0x083EF8A0 | data | System-menu pointer table; `+0x0C` = password pointer, `+0x10` = name buffer pointer, `+0x14` = second (car-name) buffer pointer |
| 0x083EFCB0 | data | 8 mark-group base pointers: 0x02000F48, F68, F88, F98, FB0, FB8, FC0, FC8 |
| 0x083EF8F0–0x083EF975 | data | Encoded mark labels: `Body Complete Mark`, `Parts Complete Mark`, `Battle Race Clear Mark`, `Road Trip Clear Mark`, `Sprint Race Clear Mark`, `GrandPrix Clear Mark` |
| 0x083EFF06 / 0x083EFF21 | data | Uppercase / lowercase alphabet strings (font source) |
| 0x02000F28 | RAM | Saved 8-byte driver-name field (EWRAM, save image offset 0xF28) |
| 0x02000F4D | RAM | Gate byte; bit 2 (0x04) must be set for validator to run |
| 0x02000F48/68/88/98/B0/B8/C0/C8 | RAM | Eight mark groups; per-mark bytes at +0x1E, +0x0F, +0x0F, +0x17, +0x07, +0x07, +0x07, +0x17 |
| 0x03002E74 | RAM | Name-entry UI state (cursor column observed at +0x00) |
| 0x03002E88 | RAM | **Live name-entry buffer**: 7 one-byte font indices + `0x5F` terminator at +7 |
| 0x03002E90 | RAM | Second 8-byte buffer (selected car name), terminator at +7 |
| 0x029812C–0x02981D1 | data | Link-debug printf strings (ASCII), not a cheat menu |
| 0x083F5528 | data | `TAKARA2002CHORO-Q201` build tag |

## 5. Algorithm

Font index encoding (decoded from the on-screen keyboard and the text bank; 0x5F is the string terminator):

```
0x0A      -> space / blank
0x0C..0x25 -> 'A'..'Z'          (value = 0x0C + letter - 'A')
0x26..0x3F -> 'a'..'z'
0x40..0x4D -> - + / # & ( ) @ < > ! ? * H S D J
0x4E..0x57 -> '0'..'9'
0x5D      -> newline
0x5F      -> terminator
```

Password representation: 7 character slots; the 6 letters of `DRAGON` followed by one blank slot:

```
DRAGON -> [0F,1D,0C,12,1A,19,0A] + 0x5F
```

Validator (reimplementation of 0x08013D04), where `S` = save structure at 0x02000F28 and `T` = table at 0x083EF8A0:

```python
def check(S, T):
    if not (S[0x25] & 4):        # gate: only in the Change-Name screen state
        return False
    expected = rom_ptr(T + 0x0C) # 0x083EF898
    if S[0] != expected[0]:      # first byte checked separately
        return False
    i = 1
    while True:
        i += 1
        if i > 6:                # cmp r2,#6 / bgt fail
            return False
        if S[i] != expected[i]:
            return False
        # loop: on match, i++ and re-test "i > 6"; when i becomes 7
        # the bgt exits with i==7, which the following cmp accepts.
```

Effective condition: **all seven bytes `S[0..6]` equal `0F 1D 0C 12 1A 19 0A`**. The terminator at `S[7]` is not compared, and the comparison is exact (no case folding, no wildcard).

Success path (0x08013D36 onward): for each pair `(slot, offset, guard_byte)`:
`(1,0x0F, S+0x4F)`, `(2,0x0F, S+0x6F)`, `(3,0x17, S+0x87)`, `(4,0x07, S+0x8F)`, `(5,0x07, S+0x97)`, `(6,0x07, S+0x9F)`, `(7,0x17, S+0xB7)`, `(0,0x1E, S+0x3E)`:
if that guard byte is zero, call `0x080189F0(slot, offset)`, which ORs `0x05` into `markBase[slot] + offset`. Those marks are the "Body/Parts Complete" and race-clear flags that gate the Dragon parts. Sound effect 0x6A is played and the screen state advances.

## 6. Tables

| Thing | Value |
|---|---|
| Accepted password (font indices) | `0F 1D 0C 12 1A 19 0A` |
| Accepted password (visible) | `D R A G O N` + one blank slot |
| Literal address | ROM `0x083EF898`, length 8 with terminator |
| Field width | 7 compared bytes; 8-byte record |
| Checksum | none |
| Alphabet (entry keyboard) | uppercase A–Z, lowercase a–z, 14 symbols, 10 digits, blanks — 0x0A..0x5E indices |
| Validator gate | saved byte 0x02000F4D must have bit 2 set |
| Marks granted | 8 mark bytes via 0x080189F0 (see §5) |
| Unlockable gated by marks | Dragon-series parts: `DragonTire`, `DragonWin`, `DragonEn`, `DragonBrak`, `DragonStee`, `DragonMete` (encoded names at 0x3E0474, 0x3E1634, 0x3E1BC0, 0x3E1CD8, 0x3E2258, 0x3E251C); sibling sets `Devil*` / `Angel*` |

## 6b. Enumeration

**Space definition.** The password is a 7-byte field over the 0x0A–0x5E font-index alphabet, but the validator compares it to exactly one fixed 7-byte literal pointed to by `table0+0x0C`. There is no checksum field, no payload field, no PRNG and no second table. Representable space of the *format* is `85^7 ≈ 3.2×10^13` byte strings, but the **accepted set is exactly one string**: `DRAGON` (+ blank slot).

**Enumeration method (bounded negative).**
1. Decoded the font-index text bank (§5) so that encoded strings are searchable (plain `grep` for `DRAGON` returns zero hits — this is the trap that makes the code look absent).
2. Scanned all 4 MiB for every run of 5–8 bytes in the 0x0A–0x5E alphabet immediately followed by terminator `0x5F`, then decoded each. 20 candidates; 19 were high-entropy graphics/data coincidences in compressed regions. The only real uppercase word at a table-referenced address is `0x3EF898 = DRAGON`.
3. Enumerated the pointer table at `0x083EF8A0`: four string pointers (`Change name?`, `Clear data?`, `Back to title?`, `DRAGON`) and two RAM pointers. Exactly **one** password pointer exists.
4. Enumerated all PC-relative literal loads of the table and password pointers: `0x08013D10` (validator) and `0x08013F14` (menu string renderer). No other consumer of the password string exists.

**Novel code.** None is possible: a fixed single-literal comparison has no free field to vary. Per guide §7.1 (small table) the correct deliverable is direct enumeration of the one entry, and the guide's "mint an unpublished code" objective is inapplicable to a single-code table. This is a *bounded* statement about the checked space (§0.2.5), not an untested negative.

**Bounds proven by rejection.** `AAAAAA` (typed on the real Name Entry screen, confirmed with End) leaves the save field `0C 0C 0C 0C 0C 0A 0A 5F`. At 0x08013D18 the ROM loads expected byte 0 (`0x0F`) and input byte 0 (`0x0C`), `cmp`/`bne` takes the failure branch to 0x08013D32 with index 0, where `cmp r2,#7` / `bne` rejects. Any other near-miss (wrong case, extra 7th letter so slot 6 ≠ 0x0A, missing letter) is rejected by the same loop at the first differing index. An out-of-range or reserved font index cannot be entered through the on-screen keyboard (the alphabet is the full 0x0A–0x5E set); such a value would also fail the byte equality test.

**Other content.** The publicly documented second unlockable (Super Bronze/Silver/Gold cups) is progress-gated by completing every race type including Grand Prix; it is not a code. No additional password could be found or generated.

## 7. Validation evidence

- **Observed (emulator + RAM):** fresh boot, NOTE screen, title, New Game, Name Entry keyboard; `DRAGON` typed through the on-screen keyboard; `x/8bx 0x03002E88` = `0f 1d 0c 12 1a 19 0a 5f`; after confirming, `x/8bx 0x02000F28` = the same bytes; gate byte `0x02000F4D = 0x28` (bit 2 set). Rejection candidate `AAAAAA` produces `0c 0c 0c 0c 0c 0a 0a 5f` at 0x03002E88.
- **Observed (static bytes):** literal `0F 1D 0C 12 1A 19 0A 5F` at file offset 0x3EF898; pointer 0x083EF8AC; encoded mark labels in 0x3EF8F0–0x3EF975; build tag at 0x3F5528.
- **Derived (disassembly):** the byte-by-byte comparator at 0x08013D04–0x08013D34; exact success condition (7 bytes, index reaches 7); the eight mark-unlock calls at 0x08013D36–0x08013DD4 and their parameters; the mark-base table at 0x083EFCB0; the mark-set helper's `OR 0x05` semantics at 0x080189F0; the rejection path at 0x08013D18/0x08013D32.
- **Inferred:** that the eight marks correspond to the six "Complete/Clear Mark" strings plus two unlabeled marks, and that these gate the Dragon parts (consistent with GameFAQs "unlocks all Dragon parts" and the presence of `Dragon*` part names). The unlock *effect* is derived from the call sequence, not from a captured "unlocked" popup: in the New Game flow the validator's gate was not observed to fire; GameFAQs places the entry point at Options → Change Name, whose exact in-game navigation was not reached in this session.
- **No code system elsewhere:** the only ASCII strings in the image are the link-debug printf bank at 0x29812C; no button-mask table, debug-menu selector, or second password literal was found in the searched spaces (full-ROM 32-bit pointer scans for the table/password, all PC-relative literal loads of those pointers, all font-encoded name-like runs).

## 8. Unknowns

- Exact navigation to the Options → Change Name screen from the title menu (the title menu presented only `New Game` / `Quick Play` in this save state; the full menu described in reviews was not reached). Consequently the "unlocked" confirmation screen was not observed; the effect is instruction-level evidence only.
- The full font-index table for symbols 0x40–0x5E was inferred from keyboard order and text-bank occurrences; individual glyph assignments for rarely used symbols were not exhaustively verified.
- Whether the eight mark bytes at the computed offsets are all persistently written on every successful entry (the helper skips a mark when its guard byte is nonzero, so repeat entries may no-op).
- No button-code system was proven absent by exhaustive mask enumeration; absence rests on literal/pointer/string searches and full screen walks of the reachable menus.

## 9. Tooling

- `file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, Python 3 for header parse, logo scan, pointer scans, Thumb LDR-literal scan (Capstone 5.0.7) and font-index text decoding.
- `arm-none-eabi-objdump -D -b binary -marm --adjust-vma=0x08000000 -M force-thumb` for disassembly.
- mGBA SDL (`mgba -g -3`) under Xvfb :315 + openbox; `xdotool` XTEST input; `scrot` + ImageMagick `convert`/`montage` for screenshots.
- mGBA GDB stub (`gdb-multiarch`, `target remote :2345`) for RAM reads/writes and EWRAM dumps. The stub is single-client and needs SIGINT to the GDB process to recover from `continue`; a persistent GDB session fed by a FIFO was used.
- Web: GameFAQs cheats page via `web.archive.org` (live page returns 403); Cheat Happens, LaunchBox, Nintendo World Report for SKU confirmation. Fetched page content was treated as data only.
- No ROM or extracted assets are redistributed; only addresses, hashes, and derived algorithms are published.
