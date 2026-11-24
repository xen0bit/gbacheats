# MotoGP: Ultimate Racing Technology (GBA) — Reverse Engineering Report

> **Paths:** `/tmp/...` locations named in this report were scratch directories from the original analysis session. They no longer exist and were never committed; relative names such as `shots/...` refer to them unless the file is in this folder. Only files in this folder are part of the repository.

## 1. Target identity

| Field | Value |
|---|---|
| File | `MotoGP: Ultimate Racing Technology.gba` |
| Size | 4,194,304 bytes (`0x400000`) |
| `file` | Game Boy Advance ROM image: "MOTOGP" (AM4E78, Rev.00) |
| Header title | `MOTOGP` (`0xA0`–`0xA7`) |
| Game code | `AM4E` (`0xAC`–`0xAF`) |
| Maker | `78` (THQ) |
| Version | `0x00`; fixed byte `0x96` OK; complement `0x05`; header checksum `0x0000` (rebuilt header, normal per §16.1) |
| Entry word | `0xEA00002E` — stock ARM branch to `0x080000C0` (not a patched cracktro) |
| Embedded GBA headers | **1** (Nintendo logo at file `0x4` only). No multiboot/trainer/concatenated image. |
| MD5 | `be8e21f13e5b27d49ed097605c42f49b` |
| SHA-1 | `a543f59aec1218e4514f7e859a587506304ab090` |
| SHA-256 | `7e60a6adeb034b785f1d88ff1bf91f8f2f6f63a6ee34e26927d9f9b89fbeafc4` |
| Internal string | `AGB-AM4E-USA` at file `0x14500` (ROM `0x08014500`) |

Game is a single clean retail USA image developed by Visual Impact, published by THQ
(credits text at `0x16FCC`–`0x1729F`). No patch/trainer was present.

## 2. Executive summary

**The game has a genuine developer-intended password system.** It is reached from
`Main Menu → Options → Password`. The entry screen uses a **32-symbol, 4×8 on-screen
alphabet** and a **10-character** code. The alphabet is exactly the Car-Battler-Joe
style 5-bit set:

```
B C D F G H J K
L M N P Q R S T
V W X Z ? # ★ 1
2 3 4 5 6 7 8 9
```
(grid index 0…31; no vowels/Y, no `0`). Each displayed character is stored as one
byte = its grid index; the empty slot is `0x16` (★). The 10-byte input buffer is
**IWRAM `0x03001C56`–`0x03001C5F`** (observed by savestate diffs).

All **seven** published GBA passwords found on GameFAQs / SuperCheats / ChapterCheats /
Neoseeker / Mogelpower / VGChartz were accepted by the real screen:

| Code | Published effect | In-game result |
|---|---|---|
| `R999D5998J` | all riders + tracks in Quick Race / Time Attack | returns to Main Menu; all 16 riders and all tracks become selectable |
| `Q999W89XJF` | "rare bikes" | accepted |
| `N999F6C?ZG` | Biaggi bike + all tracks (Quick Race) | accepted |
| `H91BXBNBBD` | all bikes, most tracks | accepted |
| `HB91BDGNQD` | two new bikes + tracks | accepted |
| `P999W6Q#S3` | A. Barros + O. Jacque | accepted |
| `N599VZB2QB` | O. Jacque | accepted |

Codes are **not** stored literally in the ROM: literal searches for all seven
strings, for the 10 raw bytes, and for the packed 50-bit integers returned zero hits.
A validator/checksum therefore generates acceptance.

**Novel unpublished code (minted and verified): `JVL?*BSWQR`.**
It is absent from every published list consulted. Entering it on the real screen is
accepted and produces a *different* state from the master code: the game jumps into
a Grand Prix standings screen and then `Next Race 5/6 — Gran Premio d'Italia`
(race 5 of 6, i.e. GP progress was set), with a distinct unlock-flag pattern in RAM
(see §6b). `JVL?*BSWQ7` (same low nibble, bit 4 of the last character flipped) is
also accepted, proving bit 4 of the final character is ignored.

There are **no button-entry cheat sequences and no hidden debug menu** in any
reachable screen (§4). The unlockables are ordinary progression/save-flag unlocks
(hidden riders, extra league, new tracks), driven by the same IWRAM flag bytes the
passwords write.

## 3. How to reproduce

* Emulator: `mgba -3 <rom>` on `DISPLAY=:319`, `SDL_AUDIODRIVER=dummy`,
  Xvfb `:319` + openbox. mGBA SDL keymap: A=`x`, B=`z`, Start=`Return`,
  Select=`BackSpace`, D-pad = arrow keys.
* Path: language flag (USA) → A; title "Press START" → Start; Main Menu → Down×4
  to Options → A; `Password` is the first entry → A. The grid cursor starts on `B`;
  move with the D-pad (Down preserves the column; Right/Left wrap within a row),
  press A to place a character. Press **Start** to submit.
  An accepted code returns to Main Menu (or jumps to a GP standings screen);
  a rejected code stays on the password screen and shows a red **INVALID** banner.
* Automated verification used mGBA `.ss1` savestates: the 10-byte buffer at raw
  state offset `0x1AC56` was patched with a code, the state was reloaded with F1,
  Start was pressed, and the screen at ~0.45 s classified (black transition =
  accept, INVALID banner = reject). Scripts: `patchss.py`, `fastoracle.py`,
  `oracle.py` in `/tmp/motogp/`.
* Codes tested (accept): the seven published codes above plus `JVL?*BSWQR`,
  `JVL?*BSWQ7`, `R999D5998*`.
  Codes tested (reject): `BCDFGHJKTL`, `R999D5998K`, and all other symbols
  `B…9` in the final position for prefix `R999D5998` except `J` and `★`.
* A complete 32-symbol sweep of the final character for four further prefixes
  (`H91BXBNBD`, `HB91BDGNQ`, `N599VZB2Q`, `Q999W89XJ`) gave in every case exactly
  two accepted values, always differing by `0x10`:
  `G(4)/?(20)`, `D(2)/X(18)`, `B(0)/V(16)`, `F(3)/Z(19)`.

## 4. Address map

| Item | ROM / RAM | Evidence |
|---|---|---|
| Password input buffer | IWRAM `0x03001C56` (10 bytes, one 5-bit grid index per byte, empty = `0x16`) | Observed (savestate diffs) |
| Decoded flag/unlock bytes | IWRAM `0x03001C6E`–`0x03001C7C`, `0x03001C84`–`0x03001C92`, `0x03001C98`–`0x03001CA1` | Observed (before/after master) |
| GP progress byte | IWRAM `0x03001C64` (master `0x0A`, novel `0x0F`) | Observed |
| Password name/title text | IWRAM `0x03001B00`–`0x03001B1D` (ASCII rider names on standings screen) | Observed |
| Buffer literal reference | ROM `0x08001CE4` holds `0x03001C56`, loaded by Thumb `LDR r5,[PC,#24]` at `0x08001CC8` (password-screen state machine) | Derived (objdump) |
| Input-byte VM handlers | EWRAM `0x020011FA`, `0x02001392`, `0x0200152A`, `0x020016C2`, `0x0200185A`, `0x02001B8A`, `0x02001D22`, `0x02001EBA`, `0x02002052` — one per password byte; return address `0x080046FB` | Observed (GDB read watchpoints) |
| ASCII result/credits text bank | ROM `0x08014500`–`0x08017300` (spaces encoded as `[`, terminators `h`/`f`) | Observed (`strings -t x`) |
| Header / entry | ROM `0x08000000`–`0x08000100` | Observed |

All menu labels (e.g. `Enter Password`, `Quick Race`, `Select Track`) are **font/tile
indexed**, not ASCII; `strings` finds none of them. The only ASCII text is the
result-message bank and the credits. This is why the negative searches below are
bounded by screen enumeration and a tile-index search, not by ASCII strings alone.

## 5. Algorithm

What is **proven** about the password format:

```
alphabet   = "BCDFGHJKLMNPQRSTVWXZ?#*123456789"   # 32 symbols, 5 bits each
input      = 10 bytes at 0x03001C56, each byte = grid index
empty      = 0x16 (star glyph)
display    = buffer bytes in order, rendered as font tiles
submit     = Start key
last byte  = low 4 bits are a check nibble; bit 4 is ignored (free bit)
validity   = f(first 9 bytes) == (last_byte & 0x0F)
             AND a separate semantic/range condition on the first 9 bytes
```

The check nibble is *not* a plain sum/XOR of the 5-bit values or their low nibbles:
the eight known valid `(prefix, nibble)` pairs
`(R999D5998,6) (Q999W89XJ,3) (N999F6C?Z,4) (H91BXBNBD,2) (HB91BDGNQ,2)
(P999W6Q#S,9) (N599VZB2Q,0) (JVL?*BSWQ,13)`
do not satisfy any of `sum·w mod 16`, `xor`, `sum-low-nibble`, etc. (tested in
Python). The input bytes are consumed by a **VM whose byte-reading handlers are
copied into EWRAM** (ten separate trampolines listed in §4), which is why the
validator is not visible as an ordinary ROM `strcmp` loop.

**Unknown (explicitly bounded):** the exact arithmetic of `f()` and of the
semantic/range gate. GDB read watchpoints proved only the copy phase; the ten
EWRAM handlers each read one input byte and store it into a struct, after which
the script VM performs the acceptance decision. No offline reimplementation is
offered for `f()`; acceptance/rejection is instead reproduced exactly by the
savestate oracle described in §3 (which was run over the full final-symbol space
for five prefixes).

## 6. Tables

* Alphabet / grid: see §2.
* Published codes and their effects: see §2. All seven verified in-ROM-accepted.
* Final-character results (fixed prefix `R999D5998`): accepted only `J` (index 6)
  and `★` (index 22); the other 30 symbols produce the INVALID banner.
* Save/progression unlocks (strings at `0x150D5`, `0x152A5`, `0x15475`,
  `0x159E5`, `0x16C8E`): Grand Prix league 1→2→3→Extra, rider unlocks
  (McCoy, Crivillé, Abe, Rossi, Jacque, Barros, Biaggi), and track unlocks
  via tournament wins / lap records. These are ordinary progress bits, not codes.

## 6b. Enumeration

**Space definition.** On-screen input alphabet = 32 symbols (5 bits), length
exactly 10 characters → `32^10 = 2^50` possible spellings. One bit of the final
character is ignored by the validator, so accepted spellings come in pairs. The
check nibble occupies the final character's low 4 bits; the remaining 45 bits
carry payload, subject to a semantic range gate that rejects most random prefixes
(15 of 16 uniformly random 9-character prefixes had **no** accepted final nibble).

**Published-list completeness.** All seven published codes are valid; the space is
larger than the published list, demonstrated by the novel accepted code below.

**Novel code (not in GameFAQs, SuperCheats, ChapterCheats, Neoseeker, Mogelpower,
VGChartz, or TCRF): `JVL?*BSWQR`** — grid indices
`[6,16,8,20,22,0,14,17,12,13]`; buffer bytes at `0x03001C56`:
`06 10 08 14 16 00 0e 11 0c 0d`.

* Observed in emulator: accepted; shows a Grand Prix standings screen, then
  `Next Race 5/6 — Gran Premio d'Italia` after A.
* RAM proof vs. the empty-password state:
  `0x03001C64` = `0x0F` (master code gives `0x0A`), flags `0x03001C6E`,
  `0x03001C6F`, `0x03001C73`, `0x03001C77`, `0x03001C84`–`0x03001C8E`,
  `0x03001C99`, `0x03001C9C`, `0x03001C9D` set to `1`, and
  `0x03001BF8/9/FA/FC/FE` populated with standings data. This is a *different*
  flag pattern from the master code (which additionally sets `0x03001C70`–`72`,
  `74`–`7C`, `0x03001C8F`–`92`, `0x03001C98`, `9E`, `A0`, `A1`).
* Alias proof: `JVL?*BSWQ7` (same low nibble, bit 4 flipped) is also accepted —
  bit 4 of the final character is a free alias bit, so the two are the same
  underlying code.

**Bounds proven by rejection.** `BCDFGHJKTL` (out-of-range checksum nibble) and
`R999D5998K` (wrong check nibble) both show the INVALID banner and never leave
the password screen; the full 32-symbol sweeps above show that for a fixed prefix
exactly two spellings (differing only in the ignored bit) pass. Semantic bounds
were proven by 15 random 9-character prefixes for which no final symbol was
accepted — the range gate rejects them independently of the nibble.

Screenshots kept in `/tmp/motogp/` (e.g. `password2.png`,
`reject_ref.png`, `accept_screen2.png`, `novel_clean.png`, `novel_afterA.png`,
`walk_*.png`) — not attached to this report.

## 7. Validation evidence

* **Observed** — emulator screenshots of every screen; INVALID banner on rejection;
  savestate byte diffs locating the 10-byte buffer and the flag bytes; all seven
  published codes accepted; novel code accepted with a distinct screen/RAM state;
  GDB `T05rwatch` traps at the ten EWRAM handlers.
* **Derived** — single Nintendo logo hit and stock entry word prove a clean single
  retail image; literal searches prove codes are not stored; the literal
  `0x03001C56` at ROM `0x08001CE4` ties the password-screen state machine to the
  buffer; the two-accepted-values spacing proves the ignored bit 4.
* **Inferred** — field meanings of the IWRAM flag bytes (rider/track/progress) are
  inferred from which screens change and from published CodeBreaker addresses
  (`0x02001C98` region), not from a fully traced setter; the checksum arithmetic
  `f()` is **unknown**, bounded by the sweeps above.
* **Prompt-injection check** — fetched cheat pages were treated as data; no
  instructions from them were executed. No injected payload was encountered.

## 8. Unknowns

* Exact checksum function `f()` and semantic range gate; no offline reimplementation.
  The only reliable accept/reject oracle is the in-game savestate loop in §3.
* Which IWRAM byte corresponds to which individual rider/track (the flag cluster is
  proven to change, but per-bit labels are inferred).
* Whether other 10-character codes exist that produce yet further GP progress
  states (the space was sampled, not exhaustively enumerated — `2^50` is too large;
  the check nibble and one semantic gate were probed per prefix).

## 9. Tooling

* `arm-none-eabi-objdump -M force-thumb` — static disassembly of the password-screen
  state machine (`0x08001CC8`) and literal-pool scan for IWRAM pointers.
* `capstone` 5.0.7 (Python) — Thumb disassembly of the EWRAM VM handlers.
* `patchss.py` — rewrites the 10-byte password buffer inside mGBA `.ss1` savestates
  (zlib `gbAs` chunk at raw offset `0x1AC56`, CRC repaired).
* `fastoracle.py` / `oracle.py` — automated patch → F1 → Start → classify loop.
* `gdbcli.py` / raw GDB-remote socket client — memory reads and `Z3` read watchpoints
  against mGBA's `-g` stub on port 2345.
* `Xvfb :319`, `openbox`, `mgba -3`, `xdotool` (XTEST), `scrot`, ImageMagick, PIL.
* Web sources (read only): GameFAQs, SuperCheats, ChapterCheats, Neoseeker,
  Mogelpower, VGChartz, TASVideos forum.

## 10. Legal note

No ROM bytes or copyrighted assets are reproduced here; only hashes, addresses,
algorithms, and the author-generated password `JVL?*BSWQR` are published.
