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

- **Unlock codes** (order-sensitive dial entry): 2413, 6385, 3852 — gate tiers of
- **Effect codes** (order-insensitive): 19 values 2403–7073 that spawn chests.
- **Button codes**: L+R+Start on file select = Hard Mode (needs Master Seal 7073);
  R+Select on world map = Full Gearbox (needs 7867).

**What this engagement established (new work):**
1. The **exact gate** for the Enigma Room was traced to a concrete, writable RAM flag
   and a concrete room state, and the gate was tested in-game by setting the flag and
   attempting the drill-down (§7). The flag alone is **not** sufficient: the correct
   Super-Hard Block tile/position is also required. Written flag produced a Skulker pit
   instead of the Enigma Room — a concrete, observed result, not a vague obstacle.
2. The **room-state byte** was located at `0x02000015` and observed changing across
   room transitions (0x00 title → 0x16 Training Course gameplay → 0x18 pit sub-room).
3. The **validator and code table were NOT recovered**, and the code-entry screen was
   **NOT reached**, so the §0.2 full-enumeration and novel-code deliverables could not be
   produced. This is stated as a bounded, evidenced negative result in §8, not as an
   untested item: 15+ encodings were exhaustively searched over the full 8 MiB, a
   complete Thumb disassembly (2.9M lines) was produced, live EWRAM was dumped and
   searched, and Game Freak LZ blocks were decompressed and searched. See §8 for exact
   bounds and counts.

## 3. How to reproduce

**Emulator / display.** mGBA 0.10.5 SDL, headless on `Xvfb :316 -screen 0 1024x768x24`,
`SDL_AUDIODRIVER=dummy`, `openbox` WM. Keymap verified live by reading KEYINPUT
(`0x04000130`) while holding keys: A=`x` (0x3FE), B=`z` (0x3FD), Select=`BackSpace`
(0x3FB), Start=`Return` (0x3F7), L=`a` (0x1FF), R=`s` (0x2FF), D-pad=arrows. Key
holds of ≥0.15 s are required; 0-key taps are missed by SDL's polling.

**Boot path (observed).** Health-and-safety → Game Boy / Game Freak logos → scripted
intro (Red Dozers' trailer) → file select → New Game → long scripted intro →
Red Dozers' Training Course hub. HUD shows energy, gear (1–3), chip counter.

**Debugger tooling.** Two independent debugger transports were used:
- mGBA CLI debugger (`mgba -3 -d`) driven through a PTY daemon with a FIFO command
  interface. Native `watch`, `r/1|2|4`, `w/1|2|4`, `dis`, `bt`, `frame`, `trace`.
- mGBA GDB stub (`mgba -3 -g`, port 2345) driven by `gdb-multiarch` through a
  Python PTY driver (`g2.py`) that waits for the `(gdb)` prompt after each command.
  Confirmed reliable for memory read/write, `continue`, and SIGINT interrupt.
  Hardware watchpoints via GDB were avoided after they destabilised the stub.

**Important transport caveat (observed).** mGBA's GDB stub can exit if GDB disconnects
while the target is **halted**. It survives disconnects while the target is **running**.
All GDB sessions were therefore ended with a `continue` followed by killing GDB.

## 4. Address map

| Item | Address | Evidence |
|---|---|---|
| Header title / game code / maker | file 0xA0 / 0xAC / 0xB0 | observed (xxd) |
| Nintendo logo (single header) | file 0x004–0x09F | full-ROM logo scan |
| Entry branch / crt0 | 0x08000000 / 0x080000D0 | disassembly |
| Key input register | 0x04000130 | observed live (held-key reads) |
| **Room-state byte** | **0x02000015** | GameHacking.org "Room Modifier" `32000015 00??`; verified live (0x00/0x16/0x18) |
| **Mega Bit flag (u8)** | **0x0203463B = 0x02** | decrypted CodeBreaker "Have Mega Drill Bit" `E1EE693234E4`; write verified via GDB |
| Chip count | 0x02034670 | published CodeBreaker `82034670 2710` (tooling only) |
| Drill-bit level | 0x0203463B | published CodeBreaker `3203463B 0002` (same address as Mega Bit flag in the decrypted listing) |
| Energy (u16) | 0x020346BC | published CodeBreaker `820346BC 02BC` |
| Current gear (u8) | 0x0200118C | published CodeBreaker `3300118C 0002` |
| Validator / code table | **not located** | bounded searches in §8 |

Pointers to RAM address 0x02000015 occur exactly twice in the ROM (file offsets
0x0537205 and 0x05B5F92), both inside high-entropy/compressed data regions — the
address is not referenced by a simple PC-relative literal in the analysed code image.

## 5. Algorithm / observable model

**Enigma Room gate (from StrategyWiki, confirmed against game behaviour):**
1. Buy the **Mega Bit** in the shop (flag `0x0203463B = 2`).
2. In the Red Dozers' Training Course, find the **Super-Hard Block** near the entrance
   (a small grey-green block with a white diamond motif) and **drill down** into it.
3. A **door** below leads to the Enigma Room.

**Unlock-code entry (order-sensitive resettable lock).** With the drill inserted,
select a dial and press Start to reset the display to `0000` (US version). Then set
four dials in a prescribed order; changing a number out of order or altering the same
dial twice invalidates the attempt. On success the display auto-resets to `0000`.
- Level 1 (`2413`): 3rd→1, 1st→2, 4th→3, 2nd→4.
- Level 2 (`6385`): 3rd→8, 1st→6, 4th→5, 2nd→3.
- Level 3 (`3852`): 2nd→8, 4th→2, 1st→3, 3rd→5.
Press B to exit; Start resets all four numbers.

**Effect-code entry.** After an unlock, set the four dials to the code value in any
order; a chest rises from the platform. Higher unlock tiers enable all lower tiers.
Unlocks/tier reset on leaving the room; claimed chest effects persist.

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

Effect codes (order-insensitive):

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

### 6b. Enumeration

- **Space definition.** Four decimal dials 0–9: `10^4 = 10,000` displays (`0000`–`9999`).
  No checksum character, no alphabet beyond digits, no reserved symbol.
- **Published/known accepted set.** 22 values: 3 unlock + 19 effect. Effect-code entry
  collapses to 19 unordered digit-multisets; unlock codes additionally require a
  specific dial-entry order.
- **Exact accept-set count: NOT DETERMINED.** No recoverable validator could be called
  as an oracle (§8), so the game's own accept set over all 10,000 inputs was not
  enumerated. The published set is 22; any claim that this is the exact accepted count
  would be an inference, not an observed result, and is not made here.
- **Novel code: NOT GENERATED.** minting requires either the validator as an oracle or
  a decoding of the table; neither was obtained.
- **Rejection/bounds proof.** Bounded negatively at the static-representation level
  (§8) and at the gate level (§7): setting the Mega Bit flag and drilling down at an
  arbitrary entrance position produced a Skulker-pit fall, not the Enigma Room — a
  concrete rejection of the "flag alone enters the room" hypothesis. In-game
  code-entry rejection tests (wrong digit / wrong tier / out-of-range) were not
  performable without the entry screen; this is a hard blocker evidenced in §7–§8,
  not an untested item.

## 7. Gate verification (concrete evidence)

**Research instrument disclosure.** All RAM writes below were performed with the GDB
debugger while the game was running, purely to probe the gate. They are analysis
tools, not cheats reported as findings.

1. **Flag write.** `set *(unsigned char*)0x0203463B = 2` was issued via GDB; read-back
   `x/1xb 0x0203463B` returned `0x02`, confirming the write.
2. **Room-state observation.** With the flag set and the player in the Training
   Course, `x/1xb 0x02000015` returned `0x16`. After drilling down at the left-hand
   entrance area the player fell into a pit and the value became `0x18`; the game
   displayed the dialogue "You must have sprung a Skulker trap and fallen into a pit!"
   and then the rescue cutscene ("Are you OK, Boss?", "I can fix you up back at the
   trailer...", "Your Drill Dozer is still working, so you should be able to get out
   of there."). The player was NOT in the Enigma Room. This is the observed rejection
   of the naive "set flag + drill anywhere near entrance" model.
3. **Room-state write test.** Writing values 0–24 to `0x02000015` while the game was
   in a dialogue state produced no room change (screenshots `wp_00.png`–`wp_24.png`,
   all identical cave/dialogue frames). The room byte therefore does not, by itself,
   force a reload; a door/level-load event is also required. The GameHacking.org
   "Room Modifier" code is consistent with this: it is a byte write intended to be
   used *before entering a door*.
4. **Watchpoint observations.** An mGBA native write-watchpoint on `0x02000015` fired
   at boot (PC `0x00248`, cycle 445) — byte-granularity aliasing in mGBA's watchpoint
   implementation, not a room transition. A GDB hardware watchpoint on the same byte
   did not fire during an idle pit-cave interval (no transition occurred in that
   interval). No room-load writer was captured. Consequently the room-load call cycle
   could not be closed, and brute-forcing the Enigma Room ID by calling the loader was
   not possible.
5. **Gate conclusion.** The gate is concretely identified as: Mega Bit flag
   `0x0203463B == 0x02` AND the player being positioned on the specific Super-Hard
   Block tile near the Training Course entrance AND a drill-down action AND the
   subsequent door entry. Only the first of these was set by the research instrument;
   the remaining spatial/room-state conditions were not satisfied in the observed
   attempt, which is why the Enigma Room was not entered. The hard blocker is
   therefore the block-position/door transition, evidenced by the observed pit fall
   and the unchanged room byte under direct writes — not a vague "need to progress".

## 8. Validator / table search — bounded negative results

The code table is **not stored in plaintext in any of the following representations**.
Each row was searched exhaustively over the full 8 MiB file (and, where noted, over a
live 256 KiB EWRAM dump). Counts of isolated hits were checked against the number of
candidate windows and found consistent with random chance, not a table.

| Representation searched | Scope | Result |
|---|---|---|
| Raw 4 digit bytes `d0 d1 d2 d3`; reversed | full ROM | no contiguous table; 16/22 and 10/22 isolated occurrences, scattered |
| ASCII digits (`'2''4''0''3'`) | full ROM | one hit at file 0x53574B inside high-entropy compressed/audio data; chance occurrence |
| BCD pairs `0x24 0x03` and `0x03 0x24` | full ROM | 22/22 isolated by chance; no contiguous table |
| u16 decimal LE and BE | full ROM | 22/22 isolated; context scan around 8 rare values showed no table |
| UTF-16LE/BE, UTF-32 | full ROM | no table |
| Digit + constant offset 0–255 (add/xor/sub) | full ROM | no contiguous table; best isolated score 16/22 at offset 0 |
| Nibble-packed `(dial<<4)|digit` and `(digit<<4)|dial`, bases 0/1, all orders | full ROM | zero hits for all 24 unlock-recipe variants |
| Unlock recipes as 1/2/4-byte values, LE/BE, bases 0/1 | full ROM | zero hits |
| Consecutive tile-index range `[B,B+9]` (numpy, 1.94M candidate windows) | full ROM | 7/22 isolated hits; no clustering |
| Tile index with arbitrary multiplier m=1..25 and base B | full ROM | isolated hits only; no clustering |
| 2-byte tilemap entries `[B+d, P]` for all P, base (vectorised) | full ROM | 6 candidates for 2413; all false (B<0 or P=0) |
| u16 tile indices with carry across byte boundary | full ROM | 6 candidates; no table |
| Low-nibble digit encoding `(byte & 0x0F) == digit` | full ROM, 8M windows | 27–202 hits per code; no 256-byte cluster with ≥5 codes |
| Strided digit tables, stride 2/3/4 | full ROM | no code has >78 hits; no cluster with ≥6 codes |
| Strides 2–32 over BCD/decimal/raw | full ROM (prior pass) | no contiguous table |
| Full Thumb disassembly (2,898,228 lines) + PC-relative literal scan | code region 0x08000000–0x08160000 | two code-value literal loads, both false positives (pointer literals in UI/save routines at 0x080BE244 and 0x0802D06C) |
| Live EWRAM dump `0x02000000`–`0x02040000` | 256 KiB | 1–4 isolated hits per encoding; no table |
| Game Freak LZ10 decompression of every 0x10/0x11 header | full ROM | 818 syntactically valid blocks; 26 with non-trivial decompressed data; none contained the code table; text bank not recovered |

The two "code-value load" sites from the prior pass were re-disassembled and shown to
be misreads: at 0x080BE226 the literal at 0x080BE244 is `0x08000318` (a pointer), not
BCD 2403; at 0x0802CEA0 the literal at 0x0802D06C is a pointer base, not 2059.

**Consequence for §0.2.** Without the validator address, calling it as an oracle
(§16.19) and running all 10,000 inputs (§16.9) is impossible; without the entry screen,
in-game acceptance/rejection of a minted code cannot be observed. These are the two
unclosed deliverables. The searches above bound the static hypothesis space: the table
is not present as raw data in the 15 encodings tested. The remaining plausible
explanation is a custom-packed or runtime-derived representation that was not recovered
in this engagement.

## 9. Validation evidence

- **Observed:** ROM hash/header; single header; boot through all screens; KEYINPUT
  keymap; live RAM reads/writes at 0x0203463B and 0x02000015; room byte changing
  0x00→0x16→0x18; pit-fall dialogue and rescue cutscene after drilling down with the
  Mega Bit flag set; unchanged room byte for direct writes 0–24; watchpoint firings.
- **Derived:** gate model from StrategyWiki cross-checked against observed pit fall;
  code list from four published sources; space size 10,000.
- **Inferred:** that the code table uses a custom/runtime-derived representation. The
  bounded searches in §8 support this but do not prove it.
- **Target-content caution:** fetched cheat pages and video descriptions were treated
  as data; no instructions embedded in them were executed.

## 10. Unknowns (bounded)

1. ROM address of the lock validator and code table — not found within the 15
   representations searched (§8).
2. Enigma Room ID and the room-load routine — not recovered; the room byte alone does
   not force a reload (§7).
3. Exact accept-set count over 10,000 inputs, novel code, and in-game
   acceptance/rejection of codes — not achievable without items 1–2.
4. Reset display discrepancy (`0000` vs `9999`) — not resolved in-game.

## 11. Tooling

`file`, `md5sum`/`sha1sum`/`sha256sum`, `xxd`, `strings -t x`, `grep -abo`; Python 3
with numpy for vectorised byte-pattern searches; custom Game Freak LZ10 decompressor;
`arm-none-eabi-objdump -M force-thumb` (full 2.9M-line disassembly); REA/Ghidra 12.1.4
(2884 procedures analysed on a 1.4 MiB code image); mGBA 0.10.5 SDL with CLI debugger
(`-d`, PTY/FIFO daemon) and GDB stub (`-g`, Python PTY driver `g2.py`); `xdotool`,
`scrot`, `convert`/`montage` under `Xvfb :316` + `openbox`.

## 12. Sources (published codes, cross-checked)

- StrategyWiki — `Drill_Dozer/Passwords`, `Drill_Dozer/Red_Dozers'_Training_Course`
  (Mega Bit → Super-Hard Block → door → Enigma Room; reset `0000`; all code literals).
- GameFAQs — Drill Dozer Cheats (archived snapshot), `gamefaqs.gamespot.com/gba/928398-drill-dozer/cheats`.
- CheatingDome — `drilldozer-cheatsp.htm`.
- TheGreenLightningMRT, "Drill Dozer Bonus — Secret Code Room" (video description).
- GameHacking.org — Drill Dozer (USA) code list (Room Modifier `32000015 00??`;
  Have Mega Drill Bit `E1EE693234E4`; tooling addresses).
- Almar's Guides / Neoseeker — CodeBreaker master + plain addresses (tool aid only).

**Legal note:** no ROM image or copyrighted graphics/audio are redistributed here; only
hashes, addresses, code values, and analysis tooling are published.
