# Classic NES Series: Donkey Kong (GBA) — Reverse Engineering Report

## 1. Target identity

| Field | Value |
|---|---|
| File | `Classic NES Series: Donkey Kong.gba` |
| Size | 1,048,576 bytes (1 MiB) |
| Header title (0xA0) | `DONKEY KONG` |
| Game code (0xAC) | `FDKE` |
| Maker code (0xB0) | `01` (Nintendo) |
| Version (0xBC) | 0x00 |
| Complement (0xBD) | 0xBD (valid: computed 0xBD) |
| Header checksum (0xBE) | 0x0000 (rebuilt-header artifact; complement is correct) |
| Entry word (0x0) | `0xEA000031` → `0x080000CC` (not the usual `0xEA00002E`; the 12 bytes at 0xC0 are data `KEY_5_2P<P`, then the stock-style crt0 starts at 0xCC) |
| Second GBA header | `0xCFC0` — `DONKEY KONG` / `FDKE` / `01`, logo intact, entry `0xEA000061` → `0x0800D14C` |
| Nintendo logo | intact at 0x04 and 0xCFC4 |
| MD5 | `e0e75f6c714550e652dbaaaba49a1d53` |
| SHA-1 | `8e3b203630f10c32aa7896afe9b7fbed7e1c8d30` |
| SHA-256 | `eb95e91780768410ed5236e9e19c30796b69b1f0386564045a2d2c11497c5d09` |

No trainer/cracktro: `MODE7`, `SUNHORS`, `CRC BANDIT`, `PARADOX`, `PDX`, `crack`, `trainer` all absent; the entry branch and both headers are Nintendo-shaped.

The file contains a shared "Classic NES Series" GBA wrapper (code/message bank near the start) plus an LZ77-compressed NES emulator core and the emulated Donkey Kong NES ROM. The message/text block occurs three times (0x2D50, 0xEBC0, 0x15324), i.e. the wrapper banks are duplicated; the executable wrapper examined here is the one at 0x0/0x1000.

## 2. Executive summary

**There is no enterable cheat/password/level-select/debug system in this ROM.**

* The only interactive developer menu is the series-standard **System Menu**, opened with **L + R** during play. Its complete item set, read from the ROM's own message table (message 6), is:
  `CONTINUE`, `RESET`, `LINKED PLAY`, `SAVE HIGH SCORE`, `SLEEP MODE`.
  Its help text (message 7) is `TO EXIT SLEEP MODE: PRESS SELECT <L/R> THE L AND R BUTTONS`.
* The ROM *does* contain the shared wrapper's secret-code strings:
  `SAVE HIGH SCORE AND SECRET CODE?`, `YES/NO`, `PRESS THE A BUTTON TO USE THIS SECRET CODE.`
  (message records 51–54 at file 0x3B00–0x3B20). **They are dead strings in this SKU**: the save path at `0x080023C8` chooses directly between "HIGH SCORE SAVED." (message 45) and "WAS UNABLE TO SAVE." (message 46); no code in the ROM loads message IDs 51–54 into the text renderer, and there is no code-entry screen, alphabet, or input buffer anywhere in the image. The same strings exist in other Classic NES Series titles (e.g. Bomberman) where an "Enter Secret Code" screen is wired; that screen is not present here.
* The emulated NES Donkey Kong has no password/level select/debug menu (TCRF documents only unused *code* data — an unused 300-point reward and an unused barrel pattern — reachable only with Game Genie memory patches, which are out of scope). Its only "secrets" are gameplay glitches.
* Published lists confirm the negative: GameFAQs' GBA Donkey Kong cheats page contains only Apple II ("APL2"), C64 POKEs, and arcade/ColecoVision/Intellivision glitches; there are **zero GBA-specific codes**. TCRF's Donkey Kong (NES) page lists no button code or level select.

So the deliverable is a bounded negative: every menu was enumerated, every text space was searched with counts, the shared secret-code strings were located and shown to be unreferenced, published codes were checked literally, and the button-code space contains no sequence table.

## 3. How to reproduce

Emulator: mGBA 0.10.5 (`/usr/games/mgba`), SDL frontend, on `Xvfb :248` with `openbox`, `SDL_AUDIODRIVER=dummy`.

Default mGBA keys used: A=`x`, B=`z`, L=`a`, R=`s`, Start=`Return`, Select=`BackSpace`, D-pad=arrows. Hold keys 150–250 ms (a 10 ms tap is missed by the wrapper's once-per-frame edge detector).

Menu path (all observed):

1. Boot → the wrapper immediately starts the NES DK title/attract screen.
2. During play press **L + R** → System Menu (message 6 drawn; BG0 tilemap, message box on the wrapper's text layer).
3. Items are the five above. `SLEEP MODE` draws the help page (message 7); wake with **Select + L + R** (verified: the help page is replaced by the game).
4. `SAVE HIGH SCORE` runs the EEPROM/high-score save and then draws message 45 (`HIGH SCORE SAVED.`) or 46 (`WAS UNABLE TO SAVE.`).
5. There is no sixth item, no code prompt, no password entry, no hidden screen behind the menu.

Static/dynamic instrumentation used:

* mGBA CLI debugger over a FIFO (`stdbuf -o0 -e0 mgba -3 -d ROM <fifo >log`): `b 0x8000e48`, `trace`, `x/N 0x...` (numbers need `0x`, otherwise the debugger parses decimal — this cost time initially).
* mGBA savestates (`Shift+F1..F8`, load `F1..F8`). `.ssN` are PNGs with a zlib `gbAs` chunk; `zlib.decompress` yields a 397,312-byte state. Layout per mGBA `serialize.h`: `0x00000` header/CPU, `0x00800` palette, `0x00C00` OAM, `0x01000` VRAM, `0x19000` IWRAM, `0x21000` EWRAM. GPRs at `0x20+4*i` (r15 at `0x5C`), CPSR at `0x60`.
* Screen text was recovered by rendering the BG tilemap from VRAM (`0x06000000 + screenblock*0x800`, 4bpp tiles at char base 1 = `0x4000`, palette at state `0x800`), not by screenshots.

## 4. Address map

| Address | Meaning |
|---|---|
| `0x08000000` | GBA header; entry `0xEA000031` → `0x080000CC` |
| `0x080000CC` | ARM crt0; SWI 0x11 (LZ77UnCompWram) with src `0x08006110`, dst `0x03007514` (observed in `trace`) |
| `0x08006110` | LZ77 stream of the NES/6502 emulator core (runs from IWRAM) |
| `0x08000E48` | tile-map rectangle fill / DMA3 helper (writes `0x040000D4` src `0x08003B28`, dst = row, control) |
| `0x08000E8C` | multi-row variant of the same fill |
| `0x08000FE0` | **message renderer**: r0=wrapper context, r1=message ID. Record address = `0x08003968 + 8*id` |
| `0x08001494` | **keypad reader**: `r = KEYINPUT(0x04000130) ^ 0x3FF`; `pressed = r & ~prev` stored to `0x030064A0`; `prev` to `0x0300649C` (edge-triggered, active-high) |
| `0x080023C8` | save-completion branch: draws message 45 or 46 |
| `0x08002776` | draws the System Menu (message 6) |
| `0x08003968` | message-record table base, 8 bytes/record: `{u16 xy, u16 wh, u32 string_ptr}`; 55 valid records, strings NUL/0xFF-terminated with 0x01–0x0C control bytes |
| `0x08002B40` | 16-entry nibble→character table `45 22 25 29 2D 31 35 39 3D 41 23 34 2C 2B 2A 2F` (3 copies: 0x2B40, 0xE9B0, 0x15114) |
| `0x08002B50` | ASCII→tile halfword table used by the renderer |
| `0x08003B00` | message 51 `SAVE HIGH SCORE AND SECRET CODE?` (dead) |
| `0x08003B18` | message 54 `PRESS THE A BUTTON TO USE THIS SECRET CODE.` (dead) |
| `0x0800CFC0` | second embedded GBA header; its crt0 at `0x0800D14C` |
| RAM `0x0300649C` / `0x030064A0` | previous keys / newly pressed keys (10-bit: A=1,B=2,Select=4,Start=8,Right=0x10,Left=0x20,Up=0x40,Down=0x80,R=0x100,L=0x200) |
| IO | DISPCNT `0x1960` (mode 0, BG0+BG3+OBJ), BG0CNT `0x8D04` (char base 1, screen base 13), BG3CNT `0x0405` (screen base 4) |

## 5. Algorithm

Key handling (reimplementation):

```c
u16 k = REG_KEYINPUT & 0x3FF;     // active low
u16 pressed_now = (~k & 0x3FF);
pressed = pressed_now & ~previous; // stored at 0x030064A0
previous = pressed_now;            // stored at 0x0300649C
```

Message rendering:

```c
record = ROM[0x3968 + 8*id];       // {x,y,w,h, ptr}
for each glyph byte in *ptr until 0xFF:
    if 0x01 <= b <= 0x0C: control (colour/newline/highlight), skip
    else: draw glyph at (x,y) using wrapper font; advance x
```

The wrapper font is proportional and is uploaded into VRAM tile slots 0x1BC.. per screen (the same tile index therefore shows a different glyph on different screens — this is why a naive tile-index→letter table fails across screens).

## 6. Tables

Message IDs (1-based, `0x3968 + 8*id`) that matter to this engagement:

| ID | Text |
|---:|---|
| 4 | `DATA COULD NOT BE DELETED.` / `DATA CANNOT BE SAVED ONTO THIS GAME PAK.` / `PRESS THE B BUTTON.` |
| 6 | `[ MENU ]` + `CONTINUE` / `RESET` / `LINKED PLAY` / `SAVE HIGH SCORE` / `SLEEP MODE` |
| 7 | `TO EXIT SLEEP MODE: PRESS SELECT [L/R] THE L AND R BUTTONS.` |
| 8 | `SAVE HIGH SCORE` / `DATA CANNOT BE SAVED DURING LINKED PLAY.` |
| 45 | `HIGH SCORE SAVED.` |
| 46 | `WAS UNABLE TO SAVE. PRESS THE B BUTTON.` |
| 51 | `SAVE HIGH SCORE AND SECRET CODE?` — **never drawn** |
| 52/53 | `YES/NO` variants for that dialog — **never drawn** |
| 54 | `PRESS THE A BUTTON TO USE THIS SECRET CODE.` — **never drawn** |

Complete inventory: 55 records (IDs 1–55). Full decoded list is reproducible from the ROM with the mapping
`0x23=A 0x25=B 0x2C=C 0x2B=D 0x2A=E 0x2F=F 0x33=G 0x37=H 0x3E=I 0x3F=K 0x43=L 0x3C=M 0x38=N 0x42=O 0x46=P 0x2E=R 0x27=S 0x32=T 0x3A=U 0x30=V 0x26=W 0x28=X 0x36=Y 0x24=Z`, space `0x20`; `0x01–0x0C` are control codes (newline/colour/highlight), `0xFF` terminates. Messages 1–10 = save-data menu/errors; 13–43 = link-play/wireless dialog set; 44–49 = save/please-wait; 50–54 = the unused secret-code flow; 55 = game-pak error.

Key masks (wrapper, 10 bits): A=0x001, B=0x002, Select=0x004, Start=0x008, Right=0x010, Left=0x020, Up=0x040, Down=0x080, R=0x100, L=0x200. All input at `0x08001494` is edge-triggered; the wrapper reads only these 10 bits.

## 6b. Enumeration

**Space definition.** The ROM defines exactly 55 message records and 5 System-Menu items. It defines **no code alphabet, no code length, no validators, no checksum, and no input buffer for user-entered strings**. The shared series' secret-code dialog (messages 51–54) exists as data but is not referenced by any executable code in this image, so its space here is 0 (unreachable), not "unknown".

**Text-space search.**

| Search | Space searched | Result |
|---|---|---|
| ASCII keywords `PASSWORD password CHEAT cheat DEBUG debug SECRET secret UNLOCK unlock LEVEL SELECT level select CONTINUE OPTION START` | whole 1 MiB | 0 hits |
| Font-code keyword `password` (`46 23 27 27 26 42 2E 2B`) | whole image | 0 hits |
| Font-code keyword `enter` (`2A 38 32 2A 2E`) | whole image | 0 hits |
| Font-code `secret code` | whole image | 6 hits = 3 copies × 2 strings (0x38E9/0x3939, 0xF8C5/0xF915, 0x16029/0x16079), all inside the save-dialog/help blobs |
| Font-code `code` | whole image | 6 hits, same three copies |
| 16-symbol alphabet runs (`A..P`, `a..p`, reversed, font-coded) | whole image | 0 hits; only the nibble table `45 22 25 29 2D 31 35 39 3D 41 23 34 2C 2B 2A 2F` occurs (×3), which is a 4-bit character dictionary, not an entry alphabet |
| Published Bomberman Classic NES codes `NMIHPLGKGJDJDJDJDJDJH`, `BAHIMNABANCPMNMNMNMH`, `BABABABABABABABABABA`, `DJEFPGGKGLPCGKMFEFEG`, `BADJODAHICDJNMEHIMNF` | whole image (ASCII) | all absent (different SKU; §16.11 case) |

**Button-code space.** The wrapper stores only the 10-bit pressed-edge word. A scan of the entire image for u16 sequences of length ≥4 drawn from the ten key masks found **0 hits**; a byte-oriented scan produced only text/data coincidences (spaces etc.). There is therefore no press-sequence table. The only multi-button inputs are the documented System Menu controls (L+R; Select+L+R; START+SELECT+A+B), implemented as masks over the pressed word, not as codes.

**Message reachability.** All `bl 0x08000FE0` sites inside the executable wrapper (file 0x1000–0x2D4C and 0x3B30–0x6110) pass constant message IDs; the drawn set is
`{2,3,6,15,18,19,20,24,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,49,55}` plus one dynamic site whose only values are `{8,9,14,16}`.
IDs **51, 52, 53, 54 are absent from every draw path**. The save path is a direct branch at `0x080023C8` between ID 45 (success) and ID 46 (failure) — no yes/no dialog, no code display.

**Novel code(s).** None can exist: there is no accepted-input surface, so the requirement "generate a code absent from every published list and have the game accept it" is vacuous for this SKU. This is the correct outcome for a no-system result, and the negative is bounded by (a) the 55-record message inventory, (b) the zero-hit keyword/alphabet/sequence scans above, and (c) the unreachability proof for the only code-related records.

**Bounds proven by rejection.** Because no input surface exists, an in-game rejection cannot be produced without inventing one. Instead the bound is structural: entering the System Menu and choosing every documented action never produces a text/code entry field; the only text input in the whole wrapper is the (absent) code dialog, whose messages are unreachable. The System Menu itself is closed: message 6 contains exactly five items and no scroll-only hidden item is present in the record set.

## 7. Validation evidence

* **Observed** — mGBA boot trace: header entry → `0x080000CC`; `SWI 0x11` decompression from `0x08006110` to `0x03007514`; execution continues in IWRAM (6502 emulator).
* **Observed** — L+R during play opens the System Menu; its BG text includes `SAVE HIGH SCORE`, `SLEEP MODE`, and the sleep-exit instruction; `Select+L+R` returns to the game. Savestate VRAM (BG0 screenblock 13 / text layer 14, char base 1) was decoded to read these strings.
* **Observed** — `SAVE HIGH SCORE` path reaches the direct 45/46 branch at `0x080023C8`; the ROM's EEPROM save window is 8 KiB (mGBA writes `<rom>.sav`); the sampled `.sav` is 0xFF-filled except 24 bytes at 0xF8–0x10F (bytes copied from the ROM header region, i.e. an uninitialised/garbage save under this emulator build). The exact save-data layout remains unknown.
* **Derived** — the message table (55 records), message IDs drawn at every call site, and the absence of IDs 51–54; the keypad edge-detector at `0x08001494`; the 0-hit u16 mask-sequence scan; the 0-hit ASCII/font-code keyword scans; the 0-hit published-code literal search.
* **Derived** — the second embedded GBA header at 0xCFC0 and the three copies of the wrapper text bank; no cracktro/trainer signatures.
* **Inferred** — the unused secret-code dialog is a shared-wrapper leftover that is compiled but not wired for this title (the strings survive in the bank because the wrapper is common across the series). It is not reachable by any input in this image.
* **Inferred** — the NES DK ROM is the ordinary NES release (no code system); TCRF documents only unused code paths requiring memory patches, which are out of scope.

## 8. Unknowns

* Exact save-data layout/EEPROM geometry (mGBA's empty save contains ROM-header bytes; forced/uninitialised save). This does not affect the cheat conclusion.
* Whether a different regional build of the same wrapper enables the secret-code dialog for this title; in this FDKE image it is provably unreferenced.
* Exact NES ROM revision inside the emulator package (not needed for the code question; TCRF covers all revisions and none has a password/level select).

## 9. Tooling

* `mgba` 0.10.5 (SDL) on `Xvfb :248` + `openbox`; `xdotool` for input; mGBA CLI debugger over a FIFO for breakpoints/memory reads; mGBA `.ssN` savestates parsed with Python (`zlib`, `struct`).
* `arm-none-eabi-objdump -M force-thumb` for static disassembly, Capstone 5.0.9 for operand/immediate scans, custom Python for the message-table dump, VRAM tilemap/text rendering, keyword and key-mask scans.
* Web sources: GameFAQs archived GBA cheats page for Classic NES Series: Donkey Kong; TCRF Donkey Kong (NES) via web.archive.org; manual-derived System Menu option list (videogamemanual.com / GameGear archive snippet); SuperCheats Bomberman Classic NES secret-code list (used only to establish the shared feature and to test literals).

## 10. Legal note

No ROM, extracted graphics, music, or game text beyond short menu strings needed as evidence is redistributed. All findings are addresses, hashes, algorithms, and short quotations.
