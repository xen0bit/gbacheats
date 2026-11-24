# Drill Dozer (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Drill Dozer/Drill Dozer.gba` |
| Size | 8,388,608 bytes (0x800000, 8 MiB) |
| `file` identification | Game Boy Advance ROM image: "DRILL DOZER" (V49E01, Rev.00) |
| Header title (0xA0) | `DRILL DOZER` |
| Game code (0xAC) | `V49E` |
| Maker (0xB0) | `01` (Nintendo); Game Freak developed |
| Version (0xBC) | `0x00` (Rev.00) — USA, 2006-02-06 |
| Fixed byte (0xB2) | `0x96` |
| Entry word (0x00) | `0xEA000032` → `b 0x080000D0` (stock Game Freak crt0) |
| Header complement (0xBD) | stored `0xCD`, computed `0xE6` — rebuilt-header artifact |
| Header checksum (0xBE) | `0x0000` |
| MD5 | `14dab12e795098988d46b96885170538` |
| SHA-1 | `c1058cc2482b91204100cc8515da99aeb06773f5` |
| SHA-256 | `95b8a2b69103dcbc6fae3504d6c8d93609f3e228444749670592cefcd6bcf47f` |

Full-ROM Nintendo-logo scan finds exactly one GBA header at offset 0. Data ends near
file offset 0x0640000; 0x0640000–0x07FFFFF is zero padding. No cracktro, no
appended trainer.

## 2. Executive summary

Drill Dozer's only developer-intended cheat surface is a **4-digit combination-lock
system** in the Enigma Room (a hidden room in the Red Dozers' Training Course), plus two
item-gated button codes on the file-select and world-map screens.

- **Unlock codes** (order-sensitive dial entry): 2413, 6385, 3852.
- **Effect codes** (order-insensitive): 19 values 2403–9434 that spawn chests.
- **Button codes**: L+R+Start on file select = Hard Mode (needs Master Seal 7073);
  R+Select on world map = Full Gearbox (needs 7867).

**What this engagement established:**
1. The **exact gate** for the Enigma Room was traced to a concrete writable RAM flag and
   a concrete room state, and the gate was tested in-game (§7). The flag alone is not
   sufficient: the correct Super-Hard Block tile/position is also required. Written flag
   produced a Skulker pit instead of the Enigma Room — a concrete observed result.
2. The **room-state byte** was located at `0x02000015` and observed changing across room
   transitions (0x00 title → 0x16 Training Course gameplay → 0x18 pit sub-room).
3. The **validator and code table were NOT recovered**, and the code-entry screen was
   **NOT reached**. A second, independent pass (this retry) searched 19 additional
   encodings/transforms over the full 8 MiB, swept candidate state words and player
   coordinates, exercised the game's own menus, and tried to force a room load with
   labelled savestate RAM patches. All failed to reveal the lock screen or a code table.
   The negative is bounded and evidenced in §8; the §0.2 novel-code/bounds deliverables
   remain unclosed.

## 3. How to reproduce

**Emulator / display.** mGBA 0.10.5 SDL, headless on `Xvfb :315 -screen 0 1024x768x24`,
`SDL_AUDIODRIVER=dummy`, `openbox` WM. Keymap verified live by reading KEYINPUT
(`0x04000130`) while holding keys: A=`x` (0x3FE), B=`z` (0x3FD), Select=`BackSpace`
(0x3FB), Start=`Return` (0x3F7), L=`a` (0x1FF), R=`s` (0x2FF), D-pad=arrows. Key
holds of ≥0.15 s are required; 0-key taps are missed by SDL's polling.

**Boot path (observed).** Health-and-safety → Game Boy / Game Freak logos → scripted
intro (Red Dozers' trailer) → file select → New Game → long scripted intro →
Red Dozers' Training Course hub. HUD shows energy, gear (1–3), chip counter.

**Debugger tooling.** Two transports were used across the two passes:
- mGBA CLI debugger (`mgba -3 -d`) driven through a PTY daemon with a FIFO/unix-socket
  command interface; `continue`, `__INT__` (Ctrl-C), `r/1|2|4`, `w/1|2|4`, `x/1`,
  `watch/r|w`, `load N`, `save N`.
- mGBA GDB stub (`mgba -3 -g`, port 2345) driven by `gdb-multiarch` through a Python PTY
  driver (prior pass). Confirmed for memory read/write, `continue`, SIGINT.

**Savestate RAM patching (this pass).** mGBA `.ss1` files are PNG containers with a
zlib-compressed `gbAs` chunk. The decompressed state is 397,312 bytes; EWRAM begins at
offset `0x21000` and IWRAM at `0x19000`, so a GBA address `0x02xxxxxx` maps to state
offset `0x21000 + (addr-0x02000000)`. `ss.py` (work dir) rewrites arbitrary bytes and
rebuilds the chunk/CRC. Patched states were loaded with the debugger `load 1` command
(a single argument string; `load` with no argument is a parse error).

**Important transport caveats (observed).**
- `mgba -d` only processes debugger commands while halted; `__INT__` (Ctrl-C written to
  the pty) is required before memory reads. While running, commands echo but produce no
  output.
- mGBA's GDB stub can exit if GDB disconnects while the target is halted; all GDB
  sessions were ended with `continue` first.
- Writing arbitrary values to `0x02000015` in live gameplay crashes the core (observed
  "GBA Memory: Jumped to invalid address" after writing `0x00`), so room-ID brute force
  is not a safe probe.

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| Header title / game code / maker | file 0xA0 / 0xAC / 0xB0 | observed (xxd) |
| Nintendo logo (single header) | file 0x004–0x09F | full-ROM logo scan |
| Entry branch / crt0 | 0x08000000 / 0x080000D0 | disassembly |
| Key input register | 0x04000130 | observed live (held-key reads) |
| **Room-state byte** | **0x02000015** | 3rd party cheat indexes "Room Modifier" `32000015 00??`; verified live (0x00/0x16/0x18) |
| **Mega Bit flag (u8)** | **0x0203463B = 0x02** | decrypted CodeBreaker "Have Mega Drill Bit" `E1EE693234E4`; write verified via GDB |
| Chip count | 0x02034670 | published CodeBreaker `82034670 2710` (tooling only) |
| Drill-bit level | 0x0203463B | published CodeBreaker `3203463B 0002` (same address as Mega Bit flag in the decrypted listing) |
| Energy (u16) | 0x020346BC | published CodeBreaker `820346BC 02BC` |
| Current gear (u8) | 0x0200118C | published CodeBreaker `3300118C 0002` |
| Player/camera X (u32) | 0x0203472C, 0x02034730 | located by 3-state walk diff (values 1880→1913→1945); patching moves the viewport (screenshot `xtest`) |
| Frame/animation counter (u8) | 0x02000000 | patch sweep 0–40 produced hashes cycling with period 7 (animation phase only) |
| Validator / code table | **not located** | bounded searches in §8 |

Pointers to RAM address `0x02000015` occur exactly twice in the ROM (file offsets
0x0537205 and 0x05B5F92), both inside high-entropy/compressed data regions — the address
is not referenced by a simple PC-relative literal in the analysed code image. A Thumb
scan for writes to `base+0x15` near a `0x02000000` literal produced only candidates in
non-code data (e.g. 0x082258A9, disassembly is garbage), so no writer was recovered.

## 5. Algorithm / observable model

**Enigma Room gate (from 3rd party cheat indexes, cross-checked against game behaviour):**
1. Buy the **Mega Bit** in the shop (flag `0x0203463B = 2`).
2. In the Red Dozers' Training Course, find the **Super-Hard Block** near the entrance
   (a small grey-green block with a white diamond motif) and **drill down** into it.
3. A **door** below leads to the Enigma Room.

**Unlock-code entry (order-sensitive resettable lock).** With the drill inserted,
select a dial and press Start to reset the display (published sources disagree: 0000 vs
9999; unresolved). Then set four dials in a prescribed order; changing a number out of
order or altering the same dial twice invalidates the attempt. On success the display
auto-resets.
- Level 1 (`2413`): 3rd→1, 1st→2, 4th→3, 2nd→4. Dial order = [3,1,4,2].
- Level 2 (`6385`): 3rd→8, 1st→6, 4th→5, 2nd→3. Dial order = [3,1,4,2].
- Level 3 (`3852`): 2nd→8, 4th→2, 1st→3, 3rd→5. Dial order = [2,4,1,3].
Press B to exit; Start resets all four numbers.

**Effect-code entry.** After an unlock, set the four dials to the code value **in any
order**; a chest rises from the platform. Higher unlock tiers enable all lower tiers.
Unlocks/tier reset on leaving the room; claimed chest effects persist.

Since the four digits are compared order-insensitively, the effect-code accept set is
naturally modelled as a set of **digit multisets**, not ordered strings (§6b).

**Button codes.** L+R+Start on a blank file toggles Hard Mode (1 energy);
R+Select on the world map toggles Full Gearbox (yellow cursor).

## 6. Tables

### 6a. Published accepted codes (four independent sources agree)

Unlock codes (temporary, order-sensitive):

| Final display | Set dials in this order | Unlocks |
|---|---|---|
| 2413 | 3rd=1, 1st=2, 4th=3, 2nd=4 | Level 1 effect codes |
| 6385 | 3rd=8, 1st=6, 4th=5, 2nd=3 | Levels 1–2 |
| 3852 | 2nd=8, 4th=2, 1st=3, 3rd=5 | Levels 1–3 |

Effect codes (order-insensitive), with level and effect:

| Code | Level | Effect | Extra prerequisite |
|---|---|---|---|
| 2403 | 1 | Wallpaper: Standard | — |
| 4089 | 1 | Wallpaper: Samurai | — |
| 1814 | 1 | Wallpaper: Rock Star | — |
| 5746 | 1 | Costume: Frog Suit | — |
| 2094 | 1 | Costume: Cute Clothes | — |
| 9025 | 1 | Costume: Drill Dozer Coveralls | — |
| 9434 | 1 | Soundstone / Sound+SFX test in Save menu | Soundstone treasure |
| 7867 | 2 | Full Gearbox | all 31 treasures |
| 2059 | 2 | Wallpaper: UFO | — |
| 8785 | 2 | Wallpaper: Control Center | — |
| 4181 | 2 | Costume: Thief Threads | — |
| 2458 | 2 | Costume: Inspector Uniform | — |
| 7073 | 3 | Master Seal (enables Hard Mode) | — |
| 5074 | 3 | Wallpaper: Happy | — |
| 5716 | 3 | Costume: School Clothes | — |
| 5854 | 3 | Costume: Blue Overalls | — |
| 2828 | 3 | Costume: Stylish Skirt | — |
| 1419 | 3 | Costume: Futuristic Clothes | — |
| 2438 | 3 | Costume: Nurse Uniform | — |

Button codes:

| Effect | Input | Screen | Prerequisite |
|---|---|---|---|
| Toggle Hard Mode | hold L+R, press Start | File select | Master Seal (7073) |
| Toggle Full Gearbox | R+Select | World map | Full Gearbox (7867) |

## 6b. Enumeration

**Space definition (exact).**

- The lock has **four decimal dials**, each 0–9. Ordered display space:
  `10^4 = 10,000` values, `0000`–`9999`. No separate checksum character, no
  alphabet beyond digits, no reserved symbol in the display.
- Because every published source states that effect-code digit **order does not
  matter**, the natural partition of the effect space is by digit multiset:
  `C(10+4-1, 4) = C(13,4) = 715` multisets of four decimal digits. Each multiset
  has between 1 (e.g. `0000`) and 24 (four distinct digits, e.g. `2403`) distinct
  ordered spellings; the full ordered space is `10,000`.
- Unlock codes additionally consume an **ordered dial sequence**: 3 pairs of
  (dial index, digit) per unlock, i.e. 4 ordered (dial,digit) steps each. The three
  published unlock recipes use only two distinct dial orders, `[3,1,4,2]` (2413 and
  6385) and `[2,4,1,3]` (3852).

**Counts that are exact and established:**

| Quantity | Exact count |
|---|---|
| Ordered display space | 10,000 |
| Unordered digit-multiset space | 715 |
| Distinct published unlock codes | 3 |
| Distinct published effect codes | 19 (13 distinct digit multisets? see below) |
| Distinct published accepted values, total | **22** |
| Unlock recipes recovered from published sources | 3 (12 ordered dial steps) |
| Effect codes with prerequisites (Soundstone, Full Gearbox) | 2 |

The 19 published effect codes occupy 19 distinct digit multisets (no two published
effect codes are permutations of one another); hence the smallest defensible
lower bound on the number of accepted multisets is **19 effect multisets + 3 unlock
multisets = 22 multisets**, and the lower bound on accepted ordered displays is
higher because each distinct-digit multiset contributes up to 24 spellings if the
validator is purely order-insensitive.

**Exact accept-set count over all 10,000 inputs: NOT DETERMINED.** The validator was
not recovered (§8), so it could not be run as an oracle (guide §16.9/§16.19) and the
game's own accept set could not be enumerated. **22 is the count of *published*
accepted values, not a proved accept-set count**; any stronger claim would be an
inference and is not made here.

**Novel code (derived, not entered).** A code absent from every published list can be
minted **by permutation** from the published order-insensitive rule: e.g. `4203`
(permutation of the published `2403`, Standard Wallpaper) or `9032` (permutation of
`2094`, Cute Clothes). These spellings appear in none of the four published sources
(all lists give one canonical digit order per effect). Under the documented
order-insensitive rule they must map to the same multiset and therefore the same
reward. **Status: derived, not observed.** The entry screen was not reached (§7–§8),
so the required in-game acceptance screenshot could not be produced. A near miss such
as `4204` changes the multiset and is predicted to be rejected; this too is a
prediction, not an observed rejection.

**Bounds proven by rejection.** Not achievable in-game without the entry screen. The
following *static* bounds were proven instead (§8): the codes are not stored as any
of 34 tested raw/encoded table representations in the 8 MiB image, so no literal
comparison table of the obvious forms exists; and the in-game gate requires the
Mega Bit flag **plus** the correct block/position — writing only `0x0203463B=2` and
drilling near the entrance produced a Skulker pit, an observed rejection of the
naive "flag alone" model.

## 7. Gate verification (concrete evidence)

**Research instrument disclosure.** All RAM writes below were performed with the GDB
debugger or savestate patching while the game was running, purely to probe the gate.
They are analysis tools, not cheats reported as findings.

1. **Flag write.** `set *(unsigned char*)0x0203463B = 2` was issued via GDB; read-back
   `x/1xb 0x0203463B` returned `0x02`, confirming the write.
2. **Room-state observation.** With the flag set and the player in the Training
   Course, `x/1xb 0x02000015` returned `0x16`. After drilling down at the left-hand
   entrance area the player fell into a pit and the value became `0x18`; the game
   displayed the dialogue "You must have sprung a Skulker trap and fallen into a pit!"
   and then the rescue cutscene. The player was NOT in the Enigma Room. This is the
   observed rejection of the naive "set flag + drill anywhere near entrance" model.
3. **Room-state write test.** Writing values 0–24 to `0x02000015` while the game was
   in a dialogue state produced no room change (screenshots `wp_00.png`–`wp_24.png`,
   all identical cave/dialogue frames). Later sweeps (this pass) showed that writing
   arbitrary room values during live gameplay can also crash the core (observed
   "GBA Memory: Jumped to invalid address: B8880000" after `0x00`), consistent with
   the byte being an index into room data rather than a directly renderable scene.
4. **Watchpoint observations.** A write-watchpoint on `0x02000015` fired only on the
   debugger's own writes in the intervals observed; a read-watchpoint never fired
   while idle, confirming the byte is read at room-load time rather than per frame.
   No natural room-load writer was captured, so the room-load routine and the
   Enigma Room ID were not recovered.
5. **Alternative entry attempts (this pass).**
   - Patched the room byte to `0x17` (the obvious adjacent candidate) in a savestate
     and reloaded: the screen did not change (no reload event).
   - Patched player/camera X (`0x0203472C`/`0x02034730`) across 0–4000 in steps of 200
     with the Mega Bit flag set and drilled down at each position: 21 screenshots,
     all the same pit background (one differing only by an animation frame).
   - Swept the frame/animation byte `0x02000000` over 0–40: hashes cycled with
     period 7, confirming it is an animation phase, not a scene word.
   - Used Save menu → Exit → Yes (confirmed on-screen) to try to force a scene
     transition; the game returned to the same Save menu, so no room load occurred.
   - `mGBA -c` cheat-file loading of the widely published Master Code +
     "Have Mega Drill Bit" / raw `0203463B:02` cheats did not change RAM
     (`0x0203463B` stayed `0x00`), so the "Access All Areas" CodeBreaker code
     could not be used as a shortcut.
6. **Gate conclusion.** The gate is concretely identified as: Mega Bit flag
   `0x0203463B == 0x02` AND the player being positioned on the specific Super-Hard
   Block tile near the Training Course entrance AND a drill-down action AND the
   subsequent door entry. Only the first of these was set by the research instrument;
   the spatial/room-state conditions were not satisfied in the observed attempts.

## 8. Validator / table search — bounded negative results

The code table is **not stored in plaintext in any of the following representations**.
Each row was searched exhaustively over the full 8 MiB file (and, where noted, over a
live EWRAM dump). Counts of isolated hits were checked against the number of candidate
windows and found consistent with random chance, not a table.

| Representation searched | Scope | Result |
|---|---|---|
| Raw 4 digit bytes `d0 d1 d2 d3`; reversed | full ROM | no contiguous table; 16/22 and 10/22 isolated occurrences, scattered |
| **All 24 digit permutations** (numpy vectorised, this pass) | full ROM | best 64-byte-window cluster = 3 codes; no table |
| **All 24 permutations combined with per-position digit offset k=0..15 (add/xor/sub), 4 encodings** | full ROM | best cluster 25 hits at file 0x337A00 — inspected, it is repeating compressed graphics data, false positive |
| ASCII digits (`'2''4''0''3'`) | full ROM | one hit at file 0x53574B inside high-entropy compressed/audio data; chance occurrence |
| ASCII/numeric digits with separator byte X, strides 2/3/4 (X=0..255) | full ROM | best 2 hits (stride 2, numeric, X=0); no table |
| BCD pairs `0x24 0x03` and `0x03 0x24` | full ROM | 22/22 isolated by chance; no contiguous table |
| u16 decimal LE and BE; u32 LE/BE | full ROM | isolated hits only; best 256-byte cluster 4 codes |
| UTF-16LE/BE, UTF-32 | full ROM | no table |
| Digit + constant offset 0–255 (add/xor/sub) | full ROM | no contiguous table; best isolated score 16/22 at offset 0 |
| Nibble-packed `(dial<<4)\|digit` and `(digit<<4)\|dial`, bases 0/1, all orders | full ROM | zero hits for all 24 unlock-recipe variants |
| Unlock recipes as 1/2/4-byte values, LE/BE, bases 0/1 | full ROM | zero hits |
| Consecutive tile-index range `[B,B+9]` (numpy, 1.94M candidate windows) | full ROM | 7/22 isolated hits; no clustering |
| **Base+B digit encoding for arbitrary base B=0..246 (numpy, this pass)** | full ROM | best clusters at 0x337A80/0x337B80 — repeating compressed tile data, false positive |
| Tile index with arbitrary multiplier m=1..25 and base B | full ROM | isolated hits only; no clustering |
| 2-byte tilemap entries `[B+d, P]` for all P, base (vectorised) | full ROM | 6 candidates for 2413; all false (B<0 or P=0) |
| u16 tile indices with carry across byte boundary | full ROM | 6 candidates; no table |
| Low-nibble digit encoding `(byte & 0x0F) == digit` | full ROM, 8M windows | 27–202 hits per code; no 256-byte cluster with ≥5 codes |
| Strided digit tables, stride 2/3/4 | full ROM | no code has >78 hits; no cluster with ≥6 codes |
| **Per-position XOR/mod-10 difference patterns between all 231 code pairs** | full ROM | ≤1 isolated hit per pattern, all in audio data 0x5xxxxx; no shared key set |
| **Unary u16 transforms: 10000−c, 9999−c, XOR 0xFFFF, two's complement, digit reversal, BCD byte swap, byte swap** | full ROM | max cluster 5/22; no table |
| **Affine pack `(code*m+b) mod 65536`, m=1..4095, b∈{0,1,0xFFFF}, u16 LE/BE** | full ROM | best 14/22 at m=0x900 — inspected, a sequential u16 font/palette table, false positive |
| **Digit-entry-order sequences [1,2,3,4], [8,6,5,3], [8,2,3,5] and reversals** | full ROM | no shared cluster |
| **Thumb scan for `strb rX,[rY,#0x14/#0x15]` near a `0x02000000` literal (this pass)** | code region <0x640000 | 1 exact 4-consecutive-byte write sequence at 0x08003F24 — a graphics blit loop, not the lock |
| Full Thumb disassembly (2,898,228 lines) + PC-relative literal scan | code region 0x08000000–0x08160000 | two code-value literal loads, both false positives (pointer literals in UI/save routines at 0x080BE244 and 0x0802D06C) |
| Live EWRAM dump `0x02000000`–`0x02040000` | 256 KiB | 1–4 isolated hits per encoding; no table |
| Game Freak LZ10 decompression of every 0x10/0x11 header | full ROM | 818 syntactically valid blocks; 26 with non-trivial decompressed data; none contained the code table; text bank not recovered |

The two "code-value load" sites from the prior pass were re-disassembled and shown to
be misreads: at 0x080BE226 the literal at 0x080BE244 is `0x08000318` (a pointer), not
BCD 2403; at 0x0802CEA0 the literal at 0x0802D06C is a pointer base, not 2059.
Similarly, four close occurrences of `0x096D` (2413) at file 0x96DB5–0x96DC5 are the
pointer literals of a 5-entry Thumb jump table at `0x08096DB8`, not code constants.

**Consequence for §0.2.** Without the validator address, calling it as an oracle and
running all 10,000 inputs is impossible; without the entry screen, in-game
acceptance/rejection of a minted code cannot be observed. These are the two unclosed
deliverables. The searches above bound the static hypothesis space: the table is not
present as raw data in any of the encodings tested. The remaining plausible explanation
is a custom-packed or runtime-derived representation that was not recovered in either
pass.

## 9. Validation evidence

- **Observed:** ROM hash/header; single header; boot through all screens; KEYINPUT
  keymap; live RAM reads/writes at 0x0203463B and 0x02000015; room byte changing
  0x00→0x16→0x18; pit-fall dialogue and rescue cutscene after drilling down with the
  Mega Bit flag set; unchanged room byte for direct writes 0–24; watchpoint firings;
  crash on invalid room-byte write; state-word and X-coordinate patch sweeps;
  all static search counts reported in §8.
- **Derived:** gate model from 3rd party cheat indexes cross-checked against observed pit fall;
  code list from four published sources; space size 10,000 / 715 multisets;
  permutation-derived novel codes (§6b).
- **Inferred:** that the code table uses a custom/runtime-derived representation. The
  bounded searches in §8 support this but do not prove it.
- **Target-content caution:** fetched cheat pages, forum posts and video descriptions
  were treated as data; no instructions embedded in them were executed.

## 10. Unknowns (bounded)

1. ROM address of the lock validator and code table — not found within the encodings
   searched (§8).
2. Enigma Room ID and the room-load routine — not recovered; the room byte alone does
   not force a reload, and patching it during live gameplay can crash the core (§7).
3. Exact accept-set count over 10,000 inputs, in-game acceptance/rejection of a
   minted code, and the effect screenshots — not achievable without items 1–2.
4. Reset display discrepancy (`0000` vs `9999`) — not resolved in-game.

## 11. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo`; Python 3
with numpy 2.5.5 for vectorised byte-pattern searches (installed with
`pip3 install --break-system-packages numpy`); custom Game Freak LZ10 decompressor;
`arm-none-eabi-objdump -M force-thumb`; REA/Ghidra 12.1.4 (Ghidra import of the full
8 MiB timed out at the 330 s startup deadline; prior pass analysed 2884 procedures on
a 1.4 MiB code image); mGBA 0.10.5 SDL with CLI debugger (`-d`, PTY/unix-socket
daemon) and GDB stub (`-g`, Python PTY driver `g2.py`); custom `ss.py` savestate
RAM patcher, `statesweep.py`, `xsweep.py`, `doorsweep.py`, `encsearch.py`,
`nibscan.py`, `permsearch.py`, `diffsearch.py`, `mulscan.py`, `unary.py`,
`stride_ascii.py`, `tilesearch.py`, `findwriter.py`, `cbdec.py`; `xdotool`, `scrot`,
`convert`/`montage` under `Xvfb :315` + `openbox`.

## 12. Sources (published codes, cross-checked)

- 3rd party cheat indexes — `Drill_Dozer/Passwords`, `Drill_Dozer/Red_Dozers'_Training_Course`
  (Mega Bit → Super-Hard Block → door → Enigma Room; reset value; all code literals;
  order-insensitivity of effect codes).
- 3rd party cheat indexes — Drill Dozer Cheats (archived snapshot), 3rd party cheat indexes.
- 3rd party cheat indexes — `drilldozer-cheatsp.htm`.
- TheGreenLightningMRT, "Drill Dozer Bonus — Secret Code Room" (video description).
- 3rd party cheat indexes — Drill Dozer (USA) code list (Room Modifier `32000015 00??`;
  Have Mega Drill Bit `E1EE693234E4`; tooling addresses).
- 3rd party cheat indexes — CodeBreaker master + plain addresses (tool aid only).
- Nintendo official manual (PDF) — control mapping and menu semantics (A jump, B
  action, R/L drill, START = Save screen).
- 3rd party cheat index forum topic 3377 — confirms the community also treats room IDs as
  an open research question for this title.

**Legal note:** no ROM image or copyrighted graphics/audio are redistributed here; only
hashes, addresses, code values, and analysis tooling are published.
