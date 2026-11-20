# Ultimate Arcade Games (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `roms/Ultimate Arcade Games/Ultimate Arcade Games.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| Header title | `ULT ARCADE` |
| Game code | `BUZE5M` (code `BUZE`, maker `5M`) |
| Revision | 0x00 |
| `file(1)` | `Game Boy Advance ROM image: "ULT ARCADE" (BUZE5M, Rev.00)` |
| MD5 | `2f681730742c52625d237e610ce6de7e` |
| SHA-1 | `74650c32d727c85d5e78c903949f6937ea9f3ee7` |
| SHA-256 | `dbb2059433f630a39be774ba33c2d433105a5915d8b74d396fc834df7e6e47e9` |

**Single image**: a full-file scan for the standard 156-byte GBA Nintendo logo found exactly
one header, at file `0x0` (ROM `0x08000000`). This is *not* a concatenated multicart.
Entry word is `0xEA00002E`, fixed byte at `0xB2` is `0x96`, header checksum `0x0000`.

The title is a 12-game compilation. Games named in the ROM text bank: **Asteroid Mine,
FlipSide, Galaxy Hero, GridLock, ChipBot, Omega Force, Highway 51, Rubes Cubes, Beekeeper,
Treasure Hunter, Merchant Galactic, Milk Run**. Shell UI: *Arcade Parlor*, *Challenge Room*,
*Shopping Mall*, *Game Status*, *Options*, *Save Game*.

## 2. Executive summary

This ROM contains a **real, developer-authored level-code system**, plus a **developer debug
level menu**, but both live *inside individual games* that are gated behind the shell's
`Arcade Parlor` / `Challenge Room` entries. Those two menu rows are drawn with padlock icons
on a fresh save and on every save state reached in this engagement.

The complete text/UI substrate of the code system was reverse engineered from ROM data
(exact bases, record format, and text IDs below), and every screen reachable on a retail
start was walked with screenshots. **No code-entry screen was reachable**, so no novel code
could be entered and no in-game accept/reject could be observed. This is reported as a
**gated-feature negative with counts** (guide §16.3 case 4 / §0.2.5), *not* as "no cheats"
and not as an untested system. The on-disk artifacts that would allow a screen-level proof
(the debug menu and the level-code screen) are present and addressed; the blocker is the
shell gate, whose unlock condition was not recovered.

No GameShark / CodeBreaker / Action Replay material is reported; only in-game surfaces were
investigated.

## 3. How to reproduce

Emulator: `mgba 0.10.5` (`/usr/local/bin/mgba`) under `Xvfb :319` + `openbox`,
`SDL_AUDIODRIVER=dummy`, 3× scale. Keymap used (mGBA SDL default):
A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`, Select = `BackSpace`,
D-pad = arrow keys. Keys held 80–200 ms (100 ms taps were intermittently missed;
the game boots slowly, ~10 s to the title screen).

Screen walk performed (all observed):

1. **Title** — "ULTIMATE ARCADE GAMES / Press START" (screenshot `game_boot10.png`).
2. **Main menu** — six rows, in cyclic order: `Game Status`, `Options`, `Arcade Parlor`,
   `Challenge Room`, `Shopping Mall`, `Save Game`. `Arcade Parlor` and `Challenge Room`
   are drawn with a padlock sprite on both sides of the highlighted row.
3. **Game Status** — `Games Collected 0`, `Games Completed 0`, `Challenges Played 0`,
   `Medals Won 0`, `Played H:M:S 0:00:00`, `Overall Completion 0.0%`.
4. **Options** — `Back to Main Menu`, `Autosave (On→Off observed)`, `Music Volume 7`,
   `Sound Volume 8`, `Credits`, `Reset Game`. No cheat/level-code entry here.
5. **Shopping Mall** — shopkeeper dialogue then a 12-row purchase list. Prices observed:
   Asteroid Mine 10, FlipSide 10, Galaxy Hero 10, GridLock 10, ChipBot 10, Omega Force 15,
   Highway 51 15, Rubes Cubes 15, Beekeeper 15, Treasure Hunter 20, Merchant Galactic 20,
   Milk Run 20. Starting balance displayed: `x50`. Pressing A on a row opens
   `Purchase this? Yes/No`; confirming dims that row's coin icon.
   Exiting requires B on the list, then **B again on "Thanks for shopping with us –
   see you next time!"** (A there cycles shopkeeper tips and returns to the shop).
6. **Save Game** — writes an 8192-byte SRAM file.

Screens **not** reached: Arcade Parlor game list, Challenge Room, any game's title screen,
any game's menu, the Level Code entry screen, the debug level menu. Count of shell screens
reached: 6 (title, main, status, options, shop list+dialogue, save). Count of gated shell
rows: 2.

## 4. Address map

All addresses below are ROM addresses (`file offset + 0x08000000`) unless marked RAM/save.

| Item | Address (ROM) | Notes |
|---|---|---|
| Header | `0x08000000` | `ULT ARCADE`, `BUZE5M`, rev 0 |
| **Text bank base** | `0x0834E604` | all text offsets are relative to this |
| **Text offset table** | `0x0834E614` | `u32` entries, 4 bytes each; ID *n* at `base+16+4n` |
| Text entry header | `base + offset[n]` | `18 00 <u16 len> <5 × u32 layout>` = 24 bytes |
| Text payload | header + `0x18` | plain ASCII, length from header |
| Text terminator | after payload | `BA 0F` (sometimes `BA 0F 02`) |
| Alphabet string | `0x0835AF04` | `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789`, 36 bytes (= `0x24`) |
| `CODE ... ACCEPTED!` | `0x0835AF40` | 18 bytes |
| `CODE ... REJECTED!` | `0x0835AF6C` | 18 bytes |
| `Level Code` (UI label) | `0x0835B2BC` | |
| `   enters   accepts   cancels` | `0x0835B2E0` | button legend for the entry screen |
| ` Use level code to skip ahead ` | `0x0835B468` | |
| `Level code` | `0x0835B5B0` | |
| `LEVEL CODE: ` | `0x0835BE70` | |
| Debug menu `level (LR change lvl)` | `0x0835BF0C` | |
| Debug menu `size of level` | `0x0835BF3C` | |
| Debug menu `level speed` | `0x0835BF64` | |
| Debug menu `reload level` | `0x0835BF88` | |
| Debug menu `reset level` | `0x0835BFAC` | |
| Debug menu `test level` | `0x0835BFD0` | |
| `Cheat!` | `0x0835E3B4` | |
| Text getter (ID→header) | `0x080C79EC` | `r0` = ID, returns length/char |
| Text draw `0x80C364C(id, …)` | `0x080C364C` | calls getter + `0x080C799C` |
| Alphabet used by initials UI | `0x08014D22`, `0x0801574FE`-area | 5-char entry, not code validator |
| SRAM save | `0x0E000000` (8192 bytes on host) | big-endian fields, checksum at `0x0E` |

Save-file layout observed (host `.sav`, all integers **big-endian**):
`0x00..0x07` magic `02 5f ba be 02 9a f0 0d`; `0x0E..0x0F` checksum (`0xE748` in the
captured save); `0x10..0x13` coins (`50`); `0x14..0x17` games-collected (`1` in the
captured save); `0x20..0x23` `50`; `0x24..0x27` `42`; `0x0481..` repeated `ABC` initials
records for 12 games; `0x06CA..0x06CF` `ff 80 10 20 40 01` (likely unlock/medal flags).
Patching coins→999, games→12 and the `0x6CA` flags to `0xFF` produced a save the game
**rejected** (Game Status returned `Games Collected 0`), so the checksum at `0x0E` is live;
its algorithm was not recovered.

## 5. Algorithm (text bank — derived, exact)

The game does not store direct pointers to UI strings: a literal scan for
`0x0835AF04` / `0x0835AF40` / `0x0835AF6C` in the ROM returned **zero** hits. Instead:

```
TEXT_BASE   = 0x0834E604
TABLE_START = TEXT_BASE + 0x10 = 0x0834E614     # u32 entry[i]
offset = u32_le(TABLE_START + 4*id)
header = TEXT_BASE + offset
length = u16_le(header + 2)                     # after 18 00
string = header + 0x18                          # 5 u32 layout words precede it
terminator = string + length                    # BA 0F [02]
```

The getter at `0x080C79EC` was disassembled and matches this exactly (`lsls r2,r0,#2;
adds r0,r2,r3; ldr r2,[r0,#16]; adds r0,r2,r3; ldrh r0,[r0,#2]`, with `r3 = 0x0834E604`).

## 6. Tables

### 6.1 Code-system text IDs (all derived from the offset table)

| Text ID | String | ROM of string |
|---:|---|---|
| 791 | `ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789` (36-symbol input alphabet) | `0x0835AF04` |
| 792 | `CODE ... ACCEPTED!` | `0x0835AF40` |
| 793 | `CODE ... REJECTED!` | `0x0835AF6C` |
| 810 | `Level Code` | `0x0835B2BC` |
| 811 | `   enters   accepts   cancels` | `0x0835B2E0` |
| 820 | ` Use level code to skip ahead ` | `0x0835B468` |
| 826 | `Level code` | `0x0835B5B0` |
| 876 | `LEVEL CODE: ` | `0x0835BE70` |
| 878 | `keep editing` | `0x0835BEBC` |
| 879 | `quit to main menu` | `0x0835BEE0` |
| 880 | `level    (LR change lvl)` | `0x0835BF0C` |
| 881 | `size of level` | `0x0835BF3C` |
| 882 | `level speed` | `0x0835BF64` |
| 883 | `reload level` | `0x0835BF88` |
| 884 | `reset level` | `0x0835BFAC` |
| 885 | `test level` | `0x0835BFD0` |
| 1062 | `Cheat!` | `0x0835E3B4` |

### 6.2 Alphabet / candidate code space

The only presented alphabet for a code field is the 36 symbols
`ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789` (IDs 791; 36 bytes at `0x0835AF04`).
If the entry screen uses the same length as the adjacent initials UI (the function at
`0x08014CF0–0x08014D9A` draws five alphabet-derived glyphs), a 5-symbol code would span
`36^5 = 60,466,176` spellings; the actual code length was **not** recoverable because the
entry screen was never displayed, so this figure is an *inferred upper context*, not a
proven space size. No checksum constant, code table, or validator was found; the ROM-wide
literal search for the alphabet string and for both result strings returned exactly one
copy each, i.e. no duplicated hard-coded code table.

### 6.3 Save records

`ABC` default initials repeat at `0x0481`, `0x0489`, … `0x0691` (one 8-byte-stride record
per game), consistent with the 12-game list.

## 6b. Enumeration

**Space definition — bounded, incomplete by design.** We can bound the *surface* but not the
code space:

| Quantity | Count | Evidence |
|---|---:|---|
| Code-related text entries in bank | 17 (IDs above) | Derived from offset table |
| Input alphabets in text bank | 1 (36 symbols) | Literal search: 1 copy of the alphabet string |
| Code-table string copies in whole ROM | 0 (no second alphabet / ACCEPTED / REJECTED copy) | `rom.find` over all 4 MiB |
| Words using text ID 791 in disassembly | ≥4 functions (`0x08014D22`, `0x080574FE`, `0x08075BA`, `0x0805ADBC`, `0x0805AF40`, `0x0807 5A8E`) | LDR-literal xref scan |
| Debug level-menu entries | 6 (IDs 880–885) | Offset table |
| Shell menu rows | 6 | Observed |
| Gated shell rows | 2 (Arcade Parlor, Challenge Room) | Observed padlock sprites |
| Shop items | 12 | Observed |
| Reachable screens walked | 6 | Observed |
| Novel codes generated / accepted / rejected in-game | **0 / 0 / 0** | Gated; see below |

**Novel code**: none. Requirement §0.2.3 could not be satisfied: the only UI that accepts a
level code is inside an individual game, and the shell's `Arcade Parlor` / `Challenge Room`
rows are locked. Attempts to advance the gate legitimately (buying Asteroid Mine and Rubes
Cubes — coin icon dims, `Games Collected` becomes 1 in the saved record) did not remove the
padlocks. Attempts to force the gate by patching the SRAM (coins, games-owned, flag byte)
were rejected by the live save checksum: Game Status read back `0`.

**Bounds proven by rejection**: the only rejection observed was the **patched save**
(coins 999 / games 12 / flags `FF` → reset to `Games Collected 0`). This is a rejection of a
*save*, not of a *code*. No code-level rejection bound was obtained.

**Negative result statement (proven about the checked space, not a universal claim):**
On this exact ROM/revision, with a retail-fresh or single-purchase save, every shell screen
reachable in this engagement was enumerated and none contains a code-entry widget; the
code-entry text, alphabet, result messages and a six-entry debug menu all exist in ROM but
are reachable only through the two locked shell rows. This is guide §16.3 **type 4 (gated
feature)**. The gate's unlock predicate and return domain were not recovered, so the
negative is bounded to "no input path found from the tested save states", not "impossible".

## 7. Validation evidence

- **Observed** (emulator screenshots, saved as `*.png` in `/tmp/opencode/ultimatearcade`):
  title screen, all six main-menu rows, padlocks on both gated rows, Game Status counters,
  Options values, shop list with all 12 prices, `Purchase this? Yes/No`, dimmed owned-game
  coin icon, `Saving Game...`, rejection of the patched save (counters reset).
- **Derived** (instruction sequence / table arithmetic): text bank base `0x0834E604`,
  table at `0x0834E614`, header layout, all 17 text IDs, getter at `0x080C79EC`,
  single-copy alphabet/result strings, big-endian save fields.
- **Inferred** (labelled): 5-symbol code length (from adjacent initials UI only);
  `0x6CA..0x6CF` as unlock/medal flags; `0x0E` as live save checksum.
- **Not observed**: any code entry, any accept/reject message rendered in-game, the debug
  level menu rendered in-game, any game actually launched.

## 8. Unknowns

1. Length and field layout of the level code, and whether it is a checksum, a table lookup,
   or a direct level index. No validator was located.
2. Exact value the shell checks to unlock `Arcade Parlor` / `Challenge Room`, and whether a
   legitimate input path reaches it. (Purchase + save did not; SRAM patch was checksum-rejected.)
3. Save checksum algorithm at `0x0E` (three algorithms tested — sum8, CRC-16/CCITT,
   BE/LE word sums over several ranges — none reproduced `0xE748`).
4. Which game hosts the `CODE ... ACCEPTED!/REJECTED!` pair; nearby text suggests the
   Rubes Cubes / cube-puzzle module, but this is inference only.
5. Whether IDs 880–885 form a reachable developer menu or vestigial text (§16.3 type 2 vs 4
   not resolved).

## 9. Tooling

- `mgba 0.10.5` under `Xvfb :319` + `openbox`, `SDL_AUDIODRIVER=dummy`; `xdotool` for input,
  `scrot` for frames, Python/Pillow for cropping.
- `strings -t x -n 4`, `xxd`, `grep`/Python byte searches.
- `arm-none-eabi-objdump -M force-thumb` for the getter/draw routines.
- Capstone (Thumb) xref scan for PC-relative literal loads of text IDs.
- Python zlib PNG `gbAs` chunk decoder for savestate RAM dumps (guide §16.13).
- A brute-force base search over the offset tables recovered `0x0834E604` by requiring
  consecutive entries to resolve to printable ASCII in the text bank.
- Web recon: `websearch` returned no results for this title; DuckDuckGo HTML returned a
  CAPTCHA; Bing returned unrelated "Ultimate" hits. Therefore **no published code list
  exists in the checked sources**, and any generated code would have been novel by default.
  Fetched pages were treated strictly as data; no instructions in them were followed.

## 10. Legal note

No ROM bytes, graphics, music or extracted assets are reproduced here. Only hashes,
addresses, algorithms, counts and the analyst's own observations are published.
