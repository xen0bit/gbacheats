# Monster Trucks (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Monster Trucks.gba` (same folder as this report) |
| Size | 4,194,304 bytes (0x400000) |
| `file` | Game Boy Advance ROM image: "MONSTERTRUCK" (BMCE5G, Rev.00) |
| Header title | `MONSTERTRUCK` |
| Game code | `BMCE` (serial AGB-BMCE-USA / AGB-BMCP-EUR, confirmed on 3rd party cheat indexes game 5398) |
| Maker | `5G` |
| Version / complement | 0x00 / 0x0D |
| Header checksum | 0x0000 (stored) vs 0x05DA (computed) — rebuilt-header artifact; entry branch is stock |
| CRC32 | `4A72170A` (matches published identity) |
| MD5 | `4f69da882dd1b399cc9dda3b4681fec7` |
| SHA-1 | `556c74e4676ff53bf3a31e0e6c3b08009bba8581` |
| SHA-256 | `df68636dfb5ead8d044414aabeb82f60931645536e20db51869bf3e4c5cd0595` |

**Phase 0 / patch check.** One Nintendo-logo hit only, at file 0x4 (the normal header); no embedded
second GBA header, no multiboot stub, no appended trainer. Entry word is `0xEA00002E`
(`b 0x080000C0`) — the stock crt0 branch, not a scene-patched cracktro. The 0x0000 header
checksum and non-complementing 0x0D byte indicate a rebuilt header, but no code patch or
trainer was detected. Save type is SRAM (`0x0E000000`, 9 literal references in ROM).

## 2. Executive summary

**No developer-intended cheat system exists in this ROM.** There is no password screen,
no button-code sequence, no hidden/debug menu, no hidden truck or track, and no
cheat/unlock entry point. The game offers exactly two top-level modes (Quick Game, Career
Mode), a 10-entry track selector, a 5-item mod shop, and an in-race pause menu. All are
reachable by normal input; all were walked with screenshots and savestate RAM evidence.

The negative is *bounded*, not assumed:
* the game's entire ASCII text bank (0x10350–0x10580) was decoded — it contains only track
  names, prize values and menu labels;
* `PASSWORD`, `CHEAT`, `DEBUG`, `SECRET`, `UNLOCK`, `MUSIC`, `PAUSE` were searched in the
  full 4 MiB in **raw ASCII, lowercase, UTF-16LE, UTF-16BE, reversed, all 256 single-byte
  shift offsets, XOR 0x55/0xAA/0xFF, and every LZ77 block** — zero hits in every encoding;
* the 13 keypad-reading routines were disassembled and every compared key mask enumerated —
  all are ordinary single-key / "any-of-these" menu-navigation tests; no key-history
  buffer, mask-sequence table, or gate flag write exists;
* the only published codes for this exact SKU are GameShark/Action Replay memory patches
  (3rd party cheat indexes), which are outside the in-game-cheat scope; the well-known
  `9LH5F76543Q5HZT05QP2` belongs to the *different* game Monster Trucks Mayhem and is absent
  from this ROM (0 literal hits).

Classification per guide §16.3: this is a **no-system** result (case 1), not dead code, a cut
feature, or a gated feature.

## 3. How to reproduce

* Emulator: mGBA (SDL build), `Xvfb :316 -screen 0 1024x768x24`, `openbox`,
  `SDL_AUDIODRIVER=dummy`, launched `mgba -3 "Monster Trucks.gba"` on `DISPLAY=:316`.
* Keymap used (mGBA SDL defaults): A = `x`, B = `z`, L = `a`, R = `s`, Start = `Return`,
  Select = `BackSpace`, D-pad = arrow keys. Holds of 60–150 ms.
* Menu paths walked:
  * Title (`PRESS START`) → Start → main menu (`QUICK GAME` / `CAREER MODE`).
  * `QUICK GAME` → `CHOOSE TRACK` (10 entries, wrap-around ring) → race.
  * In race → Start → pause (`CONTINUE` / `MUSIC: ON` / `QUIT`) → `QUIT` →
    `ARE YOU SURE YOU WANT TO QUIT?` (`YES`/`NO`) → `YES` → main menu.
  * `CAREER MODE` → `MOD SHOP` (`AVAILABLE CASH $500`; ENGINE/TURBO/TIRES/SHOCKS
    $200, NITROUS $100) → `DONE` → `NEXT TRACK` (Swampland / Track 1, `1ST $400`,
    `2ND $200`) → `OKAY` → race.
  * Button-code probes at title and menus: Konami sequence
    (↑↑↓↓←→←→BA), A+B+Start, L+R+Start — all rejected (no state change).
* Codes tested: `9LH5F76543Q5HZT05QP2` (Monster Trucks Mayhem password) — literal absent
  from ROM, so not applicable to this SKU; no in-game code screen exists to enter it.

## 4. Address map

| Item | ROM file offset / VA | Note |
|---|---|---|
| GBA header | 0x000–0x1FF | single header, stock entry |
| ASCII text bank | 0x10350–0x10580 (VA `0x08010350`–`0x08010580`) | NUL-terminated lowercase ASCII, drawn as capitals |
| Text-bank offset table | ~0x10C80–0x10E40 (VA `0x08010C80`+) | 32-bit pointers into the bank, e.g. `0x08010384` at file 0x10D6C |
| Font / glyph tile data | 0x1C7F48 onward (VA `0x081C7F48`+) | 4bpp 8×8 tiles, 0x20-byte stride; copied to VRAM (matches tile 0x078 at file 0x1C8E48) |
| Keypad handler literals | file 0x21A4, 0x25D8, 0x2828, 0x2D68, 0x2FC4, 0x3234, 0x33B4, 0x37B4, 0x3C2C, 0x3FC0, 0x43E8, 0x4AA8, 0x4BB0 | each is a `ldr` of `0x04000130` (KEYINPUT) |
| Example main-menu input loop | VA `0x08002152`–`0x08002300` | computes `pressed = ~KEYINPUT & ~old`, stores pressed/held at `[r4]`/`[r4+2]` |
| SRAM save literals | file 0x117F5, 0x12056, … (9 hits) | save base `0x0E000000` |

Savestate (`Monster Trucks.ssN`, PNG with zlib `gbAs` chunk, 397,312 bytes decompressed)
interpretation used for RAM evidence (guide §16.13): CPU/header at 0x00000, palette at
0x00800, VRAM at 0x01000, IWRAM at 0x19000 (maps `0x03000000`), EWRAM at 0x21000
(maps `0x02000000`). States were captured at title (ss1), race (ss2/ss3), pause (ss4),
main menu (ss5), track select (ss6) and mod shop (ss7). Distinct RAM values were observed,
e.g. IWRAM `0x03007270` = `0xFFFF` (title), `0x0068` (race), `0x0100`/`0x0108` (main/
track), `0x0158` (mod shop); IWRAM `0x0300538` = `0x000C` / `0x0029` / `0x0041` /
`0x0056` / `0x0019` for title / pause / main / track / mod-shop respectively. These are
**observed** per-screen differences; their semantic names were not established.

## 5. Algorithm

Not applicable — no password validator, checksum, encoder, or key sequence exists to
reverse. For completeness, the only "algorithm" found is the standard input pipeline
observed at VA `0x08002152`:

```
KEYINPUT (0x04000130, active-low)
  -> current = ~KEYINPUT & 0xFFFF            ; active-high
  -> pressed = current & ~previous
  -> store pressed at [state+0], current at [state+2]
  -> menu code: if (pressed & MASK) != 0 take action
```

Every `MASK` used in the 13 handlers is listed in §6. No branch compares a multi-press
history, no accumulator/checksum is updated, and no cheat flag word is written.

## 6. Tables

### 6.1 Full ASCII text bank (0x10350–0x10580), decoded

`Vehicle`, `ThSprite`, `SysTask`, `SysSprite` (length-prefixed C++ RTTI-style engine
object names), `swampland`, `cooks county`, `american`, `orange county`, `champion`,
`arena`, `raceway`, `racegrounds`, `track 1`…`track 10`, `1st $400`…`1st $800`,
`2nd $200`…`2nd $400`, `1/4`, `00:00.0`, `season 1 complete`, `career earnings`,
`continue`, `press start`, `quick game`, `career mode`, `back`, `select`,
`choose track`, `okay`, `next track`, `buy`, `done`, `mod shop`, `available cash`,
`4game`, `Car`, `Atv`. Nearby 0x109FC–0x10ABC are C++ runtime strings
(`bad_alloc`, `type_info`, `exception`, `_sbrk: Heap and stack collision`) — not game text.

**No password, cheat, code, secret, unlock, debug or bonus string exists in this bank.**

### 6.2 Track enumeration (observed in `CHOOSE TRACK`, all selectable)

| # | Displayed name | # | Displayed name |
|---|---|---|---|
| 1 | Swampland | 6 | Swampland |
| 2 | Cooks County Arena | 7 | Cooks County Arena |
| 3 | American Raceway | 8 | American Raceway |
| 4 | Orange County Racegrounds | 9 | Orange County Racegrounds |
| 5 | Champion Raceway | 10 | Champion Raceway |

Ten entries, five art themes reused twice. No 11th/secret track string or sprite set was
found; the selector wraps 1↔10.

### 6.3 Mod-shop enumeration (observed, 5 entries, wrapping)

ENGINE $200, TURBO $200, TIRES $200, SHOCKS $200, NITROUS $100. Selection wraps after
NITROUS. No sixth item or hidden purchase.

### 6.4 Key masks in all 13 keypad handlers (active-high; "+" = OR / any-of)

| Handler (file) | Masks tested |
|---|---|
| 0x21A4 | 0x40 Up, 0x80 Down, 0x03 A\|B, 0x30 Left\|Right, 0x08 Start |
| 0x25D8 | 0x40 Up, 0x80 Down, 0x03 A\|B |
| 0x2828 | 0x60 Up\|Left, 0x94 Down\|Right\|Select, 0x0B A\|B\|Start |
| 0x2D68 | 0x08 Start |
| 0x2FC4, 0x3234, 0x4AA8, 0x4BB0 | 0x09 A\|Start |
| 0x33B4 | 0x08 Start |
| 0x37B4 | 0x02 B, 0x40 Up, 0x80 Down |
| 0x3C2C | 0x02 B, 0x40 Up, 0x80 Down, 0x01 A |
| 0x3FC0 | 0x02 B, 0x01 A |
| 0x43E8 | 0x40 Up, 0x80 Down, 0x20 Left |

These are menu navigation/confirm tests, not cheat sequences. A 3-position cursor in the
0x21A4 handler corresponds to the pause menu's three rows (CONTINUE / MUSIC / QUIT), not a
hidden third main-menu entry — confirmed by pressing Up at the main menu (no cursor move).

## 6b. Enumeration

| Question | Space searched | Result |
|---|---|---|
| Password codes | whole 4 MiB in 9 encodings (raw/lower/UTF-16LE/BE/reverse/256 shifts/3 XORs/LZ77) for 7 critical keywords | 0 hits; no password UI screen exists |
| Button codes | all 13 `KEYINPUT` handlers; every compared mask enumerated (§6.4) | 0 history buffers, 0 sequence tables, 0 gate flags |
| Button codes — empirical | Konami, A+B+Start, L+R+Start at title and menus | 0 state changes |
| Hidden trucks | all screens + text bank | none; no truck-select screen exists in this game |
| Hidden tracks | full 10-entry selector walked + text bank | none; 10/10 reachable from a fresh save |
| Hidden/debug menu | all menus + 256-shift keyword search + LZ77 scan | none found |
| Published codes | `9LH5F76543Q5HZT05QP2` (Mayhem) literal | 0 hits — different game |
| Published codes | 3rd party cheat indexes 5398 (this SKU) | only GameShark/AR memory patches — out of scope, no in-game codes published |

Because the code space is empty, §0.2's "mint a novel unpublished code and prove bounds by
rejection" has no object. The equivalent bounded negative is delivered: the complete input
surface and the complete text/encoding space were enumerated with counts, and every
candidate code was tested or shown absent from the ROM.

## 7. Validation evidence

* **Observed**: mGBA screenshots of title, main menu, Quick Game track select (all 10
  tracks), race, pause, quit-confirmation, career mod shop (all 5 mods), career next-track,
  and title after each of three button-code probes. Savestates captured at six screen
  states with distinct RAM bytes (§4).
* **Derived**: header/logo/entry-word analysis proves a single stock image with no trainer;
  disassembly of the 13 keypad handlers proves the mask set in §6.4; literal/pointer scans
  prove the text bank and font table locations; the 9-encoding keyword scan and LZ77 scan
  prove the keyword absence.
* **Inferred**: the small on-screen words not present as ASCII (e.g. `PAUSE`, `QUIT`,
  `MUSIC: ON`, `ENGINE`) are rendered from pre-rendered font/tile graphics (font data at
  0x1C7F48+ was matched byte-for-byte to VRAM tiles). Their exact glyph-to-character table
  was not reconstructed; this does not affect the negative because no keyword for a code
  surface exists in any encoding, and all reachable screens were walked.

## 8. Unknowns

* The exact semantic names of the differing RAM words listed in §4 were not established.
* A race was entered and driven (laps, timer, position HUD observed) but the results /
  `season 1 complete` / `career earnings` screens were not reached: the truck would not
  complete a lap under the available steering inputs, so the normal-play path to those
  screens remains unexercised. They contain only progress/payment text in the decoded
  bank and are not cheat surfaces.
* The glyph-to-character table of the pre-rendered small font was not fully reconstructed.

## 9. Tooling

* `python3` (stdlib) for header/hash/CRC/literal scans, keyword encodings, LZ77 scan, and
  savestate `gbAs` decompression; Pillow for VRAM font/tile rendering.
* `strings`, `xxd`, `grep`, `arm-none-eabi-objdump -M force-thumb`, Capstone (mask scan).
* mGBA SDL + Xvfb :316 + openbox + xdotool + scrot + ImageMagick for dynamic work.
* mGBA CLI debugger (`mgba -d`, line-buffered via `stdbuf`) was available but could only
  accept commands while halted; RAM evidence therefore used savestate diffs per guide §16.13.
* Web sources consulted as data only: 3rd party cheat indexes game 5398 (identity + out-of-scope
  GameShark codes), 3rd party cheat indexes searches (no in-game codes for this SKU). No
  prompt-injection content was encountered in fetched pages.

**Legal note:** no ROM image, extracted graphics, or game assets are reproduced here; only
hashes, addresses, and the analyst's own observations are published.
